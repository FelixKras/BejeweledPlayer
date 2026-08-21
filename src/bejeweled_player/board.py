from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

import cv2
import numpy as np

Cell = tuple[int, int]
HYPERCUBE = 7
UNKNOWN_GEM = 9
FLAME_GEM_BASE = 10
STAR_GEM_BASE = 17

_HUE_TEMPLATE_BINS = {
    0: (0, 17),
    1: (4, 5, 6, 7, 8),
    2: (9, 10, 11, 12),
    3: (2, 3),
    4: (13, 14, 15, 16),
    5: (1, 2),
}


@dataclass(frozen=True)
class Move:
    start: Cell
    end: Cell
    score: int


def recognize_board(
    image: np.ndarray,
    bounds: tuple[int, int, int, int],
    rows: int,
    cols: int,
    colors: int,
) -> np.ndarray:
    if colors != 7:
        raise ValueError("the minimal recognizer supports exactly seven ordinary gem colors")
    left, top, right, bottom = bounds
    if not (0 <= left < right <= image.shape[1] and 0 <= top < bottom <= image.shape[0]):
        raise ValueError("board bounds fall outside the screenshot")

    crop = image[top:bottom, left:right]
    labels = []
    for row in range(rows):
        for col in range(cols):
            x = round((col + 0.5) * crop.shape[1] / cols)
            y = round((row + 0.5) * crop.shape[0] / rows)
            cell_size = min(crop.shape[0] // rows, crop.shape[1] // cols)
            radius = max(2, cell_size // 8)
            patch = crop[max(0, y - radius) : y + radius, max(0, x - radius) : x + radius]
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            hue, saturation, _ = np.median(hsv.reshape(-1, 3), axis=0)
            # Keep special-gem color sampling inside the gem body; cell edges include
            # board artwork and animated glows that can look falsely multicolored.
            histogram_radius = max(radius, cell_size // 4)
            histogram_patch = crop[
                max(0, y - histogram_radius) : y + histogram_radius,
                max(0, x - histogram_radius) : x + histogram_radius,
            ]
            histogram_hsv = cv2.cvtColor(histogram_patch, cv2.COLOR_BGR2HSV)
            effect_radius = max(radius, cell_size // 2)
            effect_patch = crop[
                max(0, y - effect_radius) : min(crop.shape[0], y + effect_radius),
                max(0, x - effect_radius) : min(crop.shape[1], x + effect_radius),
            ]
            effect_hsv = cv2.cvtColor(effect_patch, cv2.COLOR_BGR2HSV)
            saturated_hues = histogram_hsv[:, :, 0][histogram_hsv[:, :, 1] >= 90]
            histogram = np.histogram(saturated_hues, bins=18, range=(0, 180))[0]
            hue_families = (
                int(np.sum(histogram[0:5])),
                int(np.sum(histogram[5:9])),
                int(np.sum(histogram[9:13])),
                int(np.sum(histogram[13:18])),
            )
            sorted_families = sorted(hue_families, reverse=True)
            second_family_ratio = sorted_families[1] / max(1, sorted_families[0])
            saturated_fraction = saturated_hues.size / histogram_hsv[:, :, 0].size
            significant_hue_bins = int(np.count_nonzero(histogram > np.sum(histogram) * 0.05))
            # Confirmed rotation phases span all four dominant families, but each
            # retains at least half as much mass in a second broad hue family.
            hypercube = second_family_ratio >= 0.50 or (
                second_family_ratio >= 0.35
                and saturated_fraction < 0.70
                and significant_hue_bins >= 3
            )
            histogram_saturation = float(np.median(histogram_hsv[:, :, 1]))
            histogram_value = float(np.median(histogram_hsv[:, :, 2]))
            star_gem = (
                40 <= hue < 85
                and saturation >= 70
                and histogram_saturation < 170
                and histogram_value < 190
            )
            flame_gem = _has_flame_effect(effect_hsv)
            if (
                saturation >= 70
                and saturated_fraction >= 0.25
                and hypercube
                and (saturated_fraction < 0.85 or significant_hue_bins <= 2)
            ):
                label = HYPERCUBE
            elif saturation < 70:
                label = 6  # white
            else:
                label = classify_hue_histogram(histogram)
                if label == UNKNOWN_GEM:
                    label = classify_unknown_gem(histogram_patch)
                if label == UNKNOWN_GEM:
                    label = classify_hue(float(hue))
            if 0 <= label < 7 and star_gem:
                label = STAR_GEM_BASE + label
            elif 0 <= label < 7 and flame_gem:
                label = FLAME_GEM_BASE + label
            labels.append(label)
    return np.asarray(labels, dtype=np.int8).reshape(rows, cols)


def classify_hue_histogram(histogram: np.ndarray) -> int:
    """Classify an ordinary gem by correlation with hue-family templates."""
    observed = histogram.astype(np.float32)
    if float(np.sum(observed)) == 0:
        return UNKNOWN_GEM
    observed /= float(np.sum(observed))
    scores: list[tuple[float, int]] = []
    for label, bins in _HUE_TEMPLATE_BINS.items():
        template = np.zeros(18, dtype=np.float32)
        template[list(bins)] = 1.0 / len(bins)
        score = float(cv2.compareHist(observed, template, cv2.HISTCMP_CORREL))
        scores.append((score, label))
    scores.sort(reverse=True)
    best_score, best_label = scores[0]
    margin = best_score - scores[1][0]
    dominant_mass = float(np.sum(observed[list(_HUE_TEMPLATE_BINS[best_label])]))
    if best_score < 0.35 or margin < 0.08 or dominant_mass < 0.55:
        return UNKNOWN_GEM
    return best_label


def classify_unknown_gem(patch: np.ndarray) -> int:
    """Resolve an uncertain ordinary gem by combining independent color evidence."""
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    height, width = hsv.shape[:2]
    yy, xx = np.ogrid[:height, :width]
    distance = ((xx - (width - 1) / 2) / max(1, width / 2)) ** 2 + (
        (yy - (height - 1) / 2) / max(1, height / 2)
    ) ** 2
    regions = (distance <= 1.0, distance <= 0.55, distance <= 0.22)
    scores = np.zeros(7, dtype=np.float32)

    for weight, region in zip((0.20, 0.30, 0.35), regions, strict=True):
        pixels = hsv[region]
        saturated = pixels[pixels[:, 1] >= 70]
        if saturated.size == 0:
            continue
        histogram = np.histogram(saturated[:, 0], bins=18, range=(0, 180), weights=saturated[:, 1])[
            0
        ].astype(np.float32)
        histogram /= max(1.0, float(np.sum(histogram)))
        for label, bins in _HUE_TEMPLATE_BINS.items():
            scores[label] += weight * float(np.sum(histogram[list(bins)]))

    # Bright effect pixels are usually desaturated; weighting by saturation lets
    # surviving gem-colored pixels outvote white hint and flame overlays.
    saturated = hsv[:, :, 1] >= 70
    if np.any(saturated):
        hues = hsv[:, :, 0][saturated]
        weights = hsv[:, :, 1][saturated].astype(np.float32)
        total_weight = float(np.sum(weights))
        for label, bins in _HUE_TEMPLATE_BINS.items():
            bin_index = np.minimum(hues // 10, 17)
            scores[label] += 0.15 * float(np.sum(weights[np.isin(bin_index, bins)])) / total_weight

    # White has no meaningful hue, so score it from neutral bright pixels separately.
    neutral_bright = (hsv[:, :, 1] < 70) & (hsv[:, :, 2] >= 120)
    scores[6] = float(np.count_nonzero(neutral_bright)) / neutral_bright.size

    ranking = np.argsort(scores)[::-1]
    best, second = int(ranking[0]), int(ranking[1])
    if scores[best] < 0.42 or scores[best] - scores[second] < 0.12:
        return UNKNOWN_GEM
    return best


def classify_hue(hue: float) -> int:
    if hue < 4 or hue >= 170:
        return 0
    if hue < 20:
        return 5
    if hue < 40:
        return 3
    if hue < 85:
        return 1
    if hue < 130:
        return 2
    return 4


def _has_flame_effect(hsv: np.ndarray) -> bool:
    """Identify the bright orange ring surrounding a Flame Gem."""
    height, width = hsv.shape[:2]
    yy, xx = np.ogrid[:height, :width]
    distance = np.maximum(
        np.abs(xx - (width - 1) / 2) / max(1, width / 2),
        np.abs(yy - (height - 1) / 2) / max(1, height / 2),
    )
    orange = (
        (hsv[:, :, 0] >= 3) & (hsv[:, :, 0] <= 22) & (hsv[:, :, 1] >= 130) & (hsv[:, :, 2] >= 180)
    )
    ring = (distance > 0.50) & (distance < 0.85)
    center = distance < 0.40
    return float(np.mean(orange[ring])) >= 0.05 and float(np.mean(orange[center])) < 0.10


def gem_color(label: int) -> int | None:
    if 0 <= label < 7:
        return label
    if FLAME_GEM_BASE <= label < FLAME_GEM_BASE + 7:
        return label - FLAME_GEM_BASE
    if STAR_GEM_BASE <= label < STAR_GEM_BASE + 7:
        return label - STAR_GEM_BASE
    return None


def matched_cells(board: np.ndarray) -> set[Cell]:
    rows, cols = board.shape
    matches: set[Cell] = set()
    for row in range(rows):
        start = 0
        for col in range(1, cols + 1):
            start_color = gem_color(int(board[row, start]))
            if col == cols or gem_color(int(board[row, col])) != start_color or start_color is None:
                if col - start >= 3:
                    matches.update((row, c) for c in range(start, col))
                start = col
    for col in range(cols):
        start = 0
        for row in range(1, rows + 1):
            start_color = gem_color(int(board[start, col]))
            if row == rows or gem_color(int(board[row, col])) != start_color or start_color is None:
                if row - start >= 3:
                    matches.update((r, col) for r in range(start, row))
                start = row
    return matches


def find_best_move(
    board: np.ndarray,
    excluded_moves: Collection[tuple[Cell, Cell]] = (),
) -> Move | None:
    rows, cols = board.shape
    baseline = matched_cells(board)
    best: Move | None = None
    best_value = -1
    for row in range(rows):
        for col in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                other = (row + dr, col + dc)
                if other[0] >= rows or other[1] >= cols:
                    continue
                if ((row, col), other) in excluded_moves:
                    continue
                first = int(board[row, col])
                second = int(board[other])
                if first == HYPERCUBE or second == HYPERCUBE:
                    move = _score_hypercube_swap(board, (row, col), other)
                    if move is not None:
                        value = move.score * 100 + 500
                        if value > best_value:
                            best = move
                            best_value = value
                    continue
                if gem_color(first) is None or gem_color(second) is None:
                    continue
                candidate = board.copy()
                candidate[row, col], candidate[other] = candidate[other], candidate[row, col]
                score = len(matched_cells(candidate) - baseline)
                value = strategic_value(candidate, score, rows - row, baseline)
                if score >= 3 and value > best_value:
                    best = Move((row, col), other, score)
                    best_value = value
    return best


def find_hypercube_move(board: np.ndarray) -> Move | None:
    """Activate a hypercube against the most frequent adjacent color."""
    best: Move | None = None
    best_count = -1
    rows, cols = board.shape
    for row, col in np.argwhere(board == HYPERCUBE):
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            other = (int(row + dr), int(col + dc))
            if not (0 <= other[0] < rows and 0 <= other[1] < cols):
                continue
            move = _score_hypercube_swap(board, (int(row), int(col)), other)
            if move is None:
                continue
            if move.score > best_count:
                best = move
                best_count = move.score
    return best


def _score_hypercube_swap(board: np.ndarray, first: Cell, second: Cell) -> Move | None:
    first_label, second_label = int(board[first]), int(board[second])
    if first_label == HYPERCUBE and second_label == HYPERCUBE:
        return Move(first, second, board.size)
    if first_label == HYPERCUBE:
        hypercube, neighbor = first, second
    elif second_label == HYPERCUBE:
        hypercube, neighbor = second, first
    else:
        return None
    color = gem_color(int(board[neighbor]))
    if color is None:
        return None
    count = sum(gem_color(int(label)) == color for label in board.flat)
    return Move(hypercube, neighbor, count)


def strategic_value(
    board: np.ndarray,
    immediate_score: int,
    top_down_bias: int = 0,
    baseline: set[Cell] | None = None,
) -> int:
    """Rank moves by points, special creation, preservation, and follow-up structure."""
    value = immediate_score * 100
    new_matches = matched_cells(board) - (baseline or set())
    if creates_hypercube(board, new_matches):
        value += 5000
    elif immediate_score == 4:
        value += 400
    value -= hypercube_blast_risk(board, new_matches) * 10_000
    value += setup_potential(board) * 3
    value += len(legal_swap_count(board))
    value += top_down_bias
    return value


def creates_hypercube(board: np.ndarray, matches: set[Cell]) -> bool:
    """Return whether the resolved swap forms a straight run of at least five."""
    for row in range(board.shape[0]):
        columns = sorted(col for matched_row, col in matches if matched_row == row)
        if _has_five_consecutive(columns):
            return True
    for col in range(board.shape[1]):
        rows = sorted(row for row, matched_col in matches if matched_col == col)
        if _has_five_consecutive(rows):
            return True
    return False


def _has_five_consecutive(values: list[int]) -> bool:
    return any(values[index + 4] - values[index] == 4 for index in range(len(values) - 4))


def hypercube_blast_risk(board: np.ndarray, activated: set[Cell]) -> int:
    """Count stored hypercubes reached by directly activated Flame and Star Gems."""
    threatened: set[Cell] = set()
    rows, cols = board.shape
    for row, col in activated:
        label = int(board[row, col])
        if FLAME_GEM_BASE <= label < FLAME_GEM_BASE + 7:
            threatened.update(
                (r, c)
                for r in range(max(0, row - 1), min(rows, row + 2))
                for c in range(max(0, col - 1), min(cols, col + 2))
            )
        elif STAR_GEM_BASE <= label < STAR_GEM_BASE + 7:
            threatened.update((row, c) for c in range(cols))
            threatened.update((r, col) for r in range(rows))
    return sum(int(board[cell]) == HYPERCUBE for cell in threatened)


def setup_potential(board: np.ndarray) -> int:
    rows, cols = board.shape
    potential = 0
    for row in range(rows):
        for start in range(cols - 3):
            window = board[row, start : start + 4]
            for color in range(7):
                if int(np.count_nonzero(window == color)) == 3:
                    potential += 1
    for col in range(cols):
        for start in range(rows - 3):
            window = board[start : start + 4, col]
            for color in range(7):
                if int(np.count_nonzero(window == color)) == 3:
                    potential += 1
    return potential


def legal_swap_count(board: np.ndarray) -> set[tuple[Cell, Cell]]:
    rows, cols = board.shape
    result: set[tuple[Cell, Cell]] = set()
    for row in range(rows):
        for col in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                other = (row + dr, col + dc)
                if other[0] >= rows or other[1] >= cols:
                    continue
                if gem_color(int(board[row, col])) is None or gem_color(int(board[other])) is None:
                    continue
                candidate = board.copy()
                candidate[row, col], candidate[other] = candidate[other], candidate[row, col]
                if len(matched_cells(candidate)) >= 3:
                    result.add(((row, col), other))
    return result


def cell_center(
    cell: Cell, bounds: tuple[int, int, int, int], rows: int, cols: int
) -> tuple[int, int]:
    left, top, right, bottom = bounds
    row, col = cell
    return (
        round(left + (col + 0.5) * (right - left) / cols),
        round(top + (row + 0.5) * (bottom - top) / rows),
    )
