import numpy as np

from bejeweled_player.board import find_best_move, find_rotating_gem_move, matched_cells


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


def test_rotating_gem_targets_adjacent_globally_most_frequent_color() -> None:
    board = np.array(
        [
            [2, 2, 2, 2],
            [1, 7, 2, 3],
            [1, 4, 5, 6],
            [0, 1, 4, 5],
        ]
    )
    move = find_rotating_gem_move(board)
    assert move is not None
    assert move.start == (1, 1)
    assert move.end == (0, 1)
    assert board[move.end] == 2
    assert move.score == 5


def test_rotating_gem_fallback_is_deterministic_on_frequency_tie() -> None:
    board = np.array([[0, 1, 2], [3, 7, 4], [5, 6, 0]])
    move = find_rotating_gem_move(board)
    assert move is not None
    assert move.start == (1, 1)
    assert move.end == (0, 1)


def test_rotating_gem_fallback_requires_an_ordinary_neighbor() -> None:
    assert find_rotating_gem_move(np.full((2, 2), 7)) is None
