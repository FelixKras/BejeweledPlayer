import numpy as np

from bejeweled_player.turn import _boards_equivalent_for_settlement


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
    previous = np.array([[1, 2, 3], [4, 5, 6]])
    current = np.array([[0, 1, 2], [3, 4, 6]])
    assert not _boards_equivalent_for_settlement(previous, current)
