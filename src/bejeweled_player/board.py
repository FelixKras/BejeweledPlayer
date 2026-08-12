from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

Cell = tuple[int, int]


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
            radius = max(2, min(crop.shape[0] // rows, crop.shape[1] // cols) // 8)
            patch = crop[max(0, y - radius):y + radius, max(0, x - radius):x + radius]
            hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            hue, saturation, _ = np.median(hsv.reshape(-1, 3), axis=0)
            if saturation < 70:
                label = 6  # white
            elif np.std(hsv[:, :, 0]) > 25:
                label = 7  # multicolor special; unsupported by the immediate planner
            elif hue < 8 or hue >= 170:
                label = 0  # red
            elif hue < 22:
                label = 5  # orange
            elif hue < 40:
                label = 3  # yellow
            elif hue < 85:
                label = 1  # green
            elif hue < 130:
                label = 2  # blue
            else:
                label = 4  # purple
            labels.append(label)
    return np.asarray(labels, dtype=np.int8).reshape(rows, cols)


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
    best_value = -1
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
                value = strategic_value(candidate, score, rows - row)
                if score >= 3 and value > best_value:
                    best = Move((row, col), other, score)
                    best_value = value
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
