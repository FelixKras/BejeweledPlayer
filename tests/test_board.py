import numpy as np

from bejeweled_player.board import cell_center, find_best_move, matched_cells


def test_matched_cells_detects_horizontal_and_vertical_runs():
    board = np.array([[1, 1, 1], [2, 3, 4], [2, 5, 6]])
    assert matched_cells(board) == {(0, 0), (0, 1), (0, 2)}


def test_find_best_move_creates_match():
    board = np.array([
        [1, 2, 1, 4],
        [3, 1, 5, 6],
        [2, 3, 4, 5],
        [4, 5, 6, 2],
    ])
    move = find_best_move(board)
    assert move is not None
    assert {move.start, move.end} == {(0, 1), (1, 1)}
    assert move.score == 3


def test_cell_center_maps_grid_to_screen():
    assert cell_center((0, 0), (100, 200, 500, 1000), 8, 8) == (125, 250)
    assert cell_center((7, 7), (100, 200, 500, 1000), 8, 8) == (475, 950)
