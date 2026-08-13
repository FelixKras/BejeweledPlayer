from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

Cell = tuple[int, int]
UNKNOWN_GEM = 9

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
    image: np.ndarray, bounds: tuple[int, int, int, int], rows: int, cols: int,
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
            patch = crop[max(0, y - radius):y + radius, max(0, x - radius):x + radius]
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            hue, saturation, _ = np.median(hsv.reshape(-1, 3), axis=0)
            # Keep special-gem color sampling inside the gem body; cell edges include
            # board artwork and animated glows that can look falsely multicolored.
            histogram_radius = max(radius, cell_size // 4)
            histogram_patch = crop[
                max(0, y - histogram_radius):y + histogram_radius,
                max(0, x - histogram_radius):x + histogram_radius,
            ]
            histogram_hsv = cv2.cvtColor(histogram_patch, cv2.COLOR_BGR2HSV)
            saturated_hues = histogram_hsv[:, :, 0][histogram_hsv[:, :, 1] >= 90]
            histogram = np.histogram(saturated_hues, bins=18, range=(0, 180))[0]
            hue_families = (
                int(np.sum(histogram[0:5])),
                int(np.sum(histogram[5:9])),
                int(np.sum(histogram[9:13])),
                int(np.sum(histogram[13:18])),
            )
            multicolor = sum(count >= max(50, saturated_hues.size * 0.12) for count in hue_families) >= 2
            histogram_saturation = float(np.median(histogram_hsv[:, :, 1]))
            histogram_value = float(np.median(histogram_hsv[:, :, 2]))
            if (
                40 <= hue < 85
                and saturation >= 70
                and histogram_saturation < 170
                and histogram_value < 190
            ):
                label = 8  # shining row-and-column special
            elif saturation >= 70 and multicolor:
                label = 7  # rotating multicolor gem
            elif saturation < 70:
                label = 6  # white
            else:
                label = classify_hue_histogram(histogram)
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


def matched_cells(board: np.ndarray) -> set[Cell]:
    rows, cols = board.shape
    matches: set[Cell] = set()
    for row in range(rows):
        start = 0
        for col in range(1, cols + 1):
            if col == cols or board[row, col] != board[row, start] or board[row, start] >= 7:
                if col - start >= 3:
                    matches.update((row, c) for c in range(start, col))
                start = col
    for col in range(cols):
        start = 0
        for row in range(1, rows + 1):
            if row == rows or board[row, col] != board[start, col] or board[start, col] >= 7:
                if row - start >= 3:
                    matches.update((r, col) for r in range(start, row))
                start = row
    return matches


def find_best_move(board: np.ndarray) -> Move | None:
    rows, cols = board.shape
    baseline = matched_cells(board)
    best: Move | None = None
    best_priority = (-1, -1)
    for row in range(rows):
        for col in range(cols):
            for dr, dc in ((0, 1), (1, 0)):
                other = (row + dr, col + dc)
                if other[0] >= rows or other[1] >= cols:
                    continue
                if board[row, col] >= 7 or board[other] >= 7:
                    continue
                candidate = board.copy()
                candidate[row, col], candidate[other] = candidate[other], candidate[row, col]
                score = len(matched_cells(candidate) - baseline)
                priority = (score, strategic_value(candidate, score, rows - row))
                if score >= 3 and priority > best_priority:
                    best = Move((row, col), other, score)
                    best_priority = priority
    return best


def find_rotating_gem_move(board: np.ndarray) -> Move | None:
    """Activate a multicolor gem against the most frequent adjacent color."""
    counts = np.bincount(board[board < 7], minlength=7)
    best: Move | None = None
    best_count = -1
    rows, cols = board.shape
    for row, col in np.argwhere(board == 7):
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            other = (int(row + dr), int(col + dc))
            if not (0 <= other[0] < rows and 0 <= other[1] < cols):
                continue
            color = int(board[other])
            if color >= 7:
                continue
            count = int(counts[color])
            if count > best_count:
                best = Move((int(row), int(col)), other, count)
                best_count = count
    return best


def strategic_value(board: np.ndarray, immediate_score: int, top_down_bias: int = 0) -> int:
    """Rank ordinary moves by points first, then useful follow-up structure."""
    value = immediate_score * 100
    if immediate_score >= 5:
        value += 1000
    elif immediate_score == 4:
        value += 400
    value += setup_potential(board) * 3
    value += len(legal_swap_count(board))
    value += top_down_bias
    return value


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
                if board[row, col] >= 7 or board[other] >= 7:
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
