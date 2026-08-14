import numpy as np

from bejeweled_player.turn import _board_changed_after_move, _boards_equivalent_for_settlement


def test_move_change_rejects_unchanged_board() -> None:
    board = np.array([[1, 2], [3, 4]])
    assert not _board_changed_after_move(board, board.copy())


def test_move_change_rejects_single_cell_flicker() -> None:
    before = np.array([[1, 2], [3, 4]])
    current = np.array([[1, 5], [3, 4]])
    assert not _board_changed_after_move(before, current)


def test_move_change_accepts_two_ordinary_changes() -> None:
    before = np.array([[1, 2], [3, 4]])
    current = np.array([[2, 1], [3, 4]])
    assert _board_changed_after_move(before, current)


def test_settlement_allows_exact_board_match() -> None:
    board = np.array([[1, 2], [3, 4]])
    assert _boards_equivalent_for_settlement(board, board.copy())


def test_settlement_allows_special_cell_flicker() -> None:
    previous = np.array([[1, 7], [3, 4]])
    current = np.array([[1, 2], [3, 4]])
    assert _boards_equivalent_for_settlement(previous, current)


def test_settlement_allows_sparse_ordinary_changes_for_animation() -> None:
    previous = np.array([[1, 2, 3], [4, 5, 6]])
    current = np.array([[0, 1, 2], [3, 5, 6]])
    assert _boards_equivalent_for_settlement(previous, current)


def test_settlement_allows_hint_and_special_flicker_together() -> None:
    previous = np.array([[1, 2, 7], [3, 4, 5]])
    current = np.array([[1, 5, 2], [6, 4, 5]])
    assert _boards_equivalent_for_settlement(previous, current)


def test_settlement_rejects_broad_ordinary_changes() -> None:
    previous = np.arange(16).reshape(4, 4) % 7
    current = (previous + 1) % 7
    assert not _boards_equivalent_for_settlement(previous, current)


def test_settlement_allows_eight_animated_cells() -> None:
    previous = np.arange(16).reshape(4, 4) % 7
    current = previous.copy()
    current.flat[:8] = (current.flat[:8] + 1) % 7
    assert _boards_equivalent_for_settlement(previous, current)
