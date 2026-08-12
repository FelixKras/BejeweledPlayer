import numpy as np

from bejeweled_player.turn import _boards_equivalent_for_settlement


def test_settlement_allows_exact_board_match() -> None:
    board = np.array([[1, 2], [3, 4]])
    assert _boards_equivalent_for_settlement(board, board.copy())


def test_settlement_allows_special_cell_flicker() -> None:
    previous = np.array([[1, 7], [3, 4]])
    current = np.array([[1, 2], [3, 4]])
    assert _boards_equivalent_for_settlement(previous, current)


def test_settlement_allows_one_ordinary_cell_flicker() -> None:
    previous = np.array([[1, 2], [3, 4]])
    current = np.array([[1, 2], [3, 5]])
    assert _boards_equivalent_for_settlement(previous, current)


def test_settlement_rejects_multiple_ordinary_changes() -> None:
    previous = np.array([[1, 2], [3, 4]])
    current = np.array([[1, 5], [6, 4]])
    assert not _boards_equivalent_for_settlement(previous, current)
