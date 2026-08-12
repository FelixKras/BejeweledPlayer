import numpy as np

from bejeweled_player.board import find_best_move, matched_cells


def test_special_cells_do_not_count_as_ordinary_matches() -> None:
    board = np.array([[1, 1, 7, 1], [2, 3, 4, 5], [3, 4, 5, 6]])
    assert matched_cells(board) == set()


def test_strategy_prefers_five_match_over_three_match() -> None:
    board = np.array(
        [
            [4, 5, 1, 2, 2, 1],
            [3, 2, 3, 1, 3, 2],
            [0, 4, 1, 5, 4, 3],
            [1, 4, 3, 5, 0, 3],
            [1, 0, 4, 3, 4, 0],
            [0, 4, 1, 5, 2, 2],
        ]
    )
    move = find_best_move(board)
    assert move is not None
    assert move.score >= 4
