import numpy as np

from bejeweled_player.board import (
    FLAME_GEM_BASE,
    STAR_GEM_BASE,
    creates_hypercube,
    find_best_move,
    find_hypercube_move,
    hypercube_blast_risk,
    matched_cells,
)


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


def test_strategy_prefers_hypercube_creation_over_larger_immediate_match() -> None:
    board = np.array(
        [
            [3, 3, 5, 3, 3, 1],
            [4, 4, 3, 0, 3, 0],
            [5, 1, 2, 4, 0, 2],
            [4, 0, 5, 1, 3, 3],
            [3, 0, 5, 1, 3, 1],
            [5, 4, 0, 0, 4, 2],
        ]
    )
    move = find_best_move(board)

    assert move is not None
    assert move.score == 5
    assert {move.start, move.end} == {(0, 2), (1, 2)}


def test_colored_specials_participate_in_ordinary_matches() -> None:
    board = np.array([[1, FLAME_GEM_BASE + 1, STAR_GEM_BASE + 1]])
    assert matched_cells(board) == {(0, 0), (0, 1), (0, 2)}


def test_detects_straight_five_as_hypercube_creation() -> None:
    board = np.array([[2, 2, 2, 2, 2], [0, 1, 3, 4, 5]])
    assert creates_hypercube(board, matched_cells(board))


def test_flame_and_star_blasts_report_stored_hypercube_risk() -> None:
    board = np.array(
        [
            [7, 0, 0, 0],
            [1, FLAME_GEM_BASE + 1, 1, 0],
            [0, 0, STAR_GEM_BASE + 2, 7],
            [0, 0, 2, 0],
        ]
    )
    assert hypercube_blast_risk(board, {(1, 1)}) == 1
    assert hypercube_blast_risk(board, {(2, 2)}) == 1


def test_hypercube_targets_adjacent_globally_most_frequent_color() -> None:
    board = np.array(
        [
            [2, 2, 2, 2],
            [1, 7, 2, 3],
            [1, 4, 5, 6],
            [0, 1, 4, 5],
        ]
    )
    move = find_hypercube_move(board)
    assert move is not None
    assert move.start == (1, 1)
    assert move.end == (0, 1)
    assert board[move.end] == 2
    assert move.score == 5


def test_hypercube_fallback_is_deterministic_on_frequency_tie() -> None:
    board = np.array([[0, 1, 2], [3, 7, 4], [5, 6, 0]])
    move = find_hypercube_move(board)
    assert move is not None
    assert move.start == (1, 1)
    assert move.end == (0, 1)


def test_hypercube_pair_clears_the_board() -> None:
    move = find_hypercube_move(np.full((2, 2), 7))
    assert move is not None
    assert move.score == 4


def test_hypercube_is_ranked_with_ordinary_moves() -> None:
    board = np.array(
        [
            [2, 2, 2, 2],
            [1, 7, 2, 3],
            [1, 4, 5, 6],
            [0, 1, 4, 5],
        ]
    )
    move = find_best_move(board)
    assert move is not None
    assert move.start == (1, 1)


def test_strategy_skips_rejected_move() -> None:
    board = np.array(
        [
            [4, 4, 0, 0, 5, 0, 1, 0],
            [0, 5, 2, 2, 5, 4, 6, 4],
            [2, 2, 6, 3, 4, 2, 3, 0],
            [0, 1, 5, 1, 4, 5, 2, 2],
            [6, 4, 4, 6, 3, 2, 5, 1],
            [0, 2, 2, 1, 4, 5, 0, 2],
            [4, 1, 1, 6, 3, 0, 1, 0],
            [2, 5, 6, 3, 1, 0, 2, 1],
        ]
    )
    rejected = find_best_move(board)
    assert rejected is not None

    alternative = find_best_move(board, {(rejected.start, rejected.end)})

    assert alternative is not None
    assert (alternative.start, alternative.end) != (rejected.start, rejected.end)
