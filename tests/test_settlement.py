from pathlib import Path
from collections import deque

import cv2
import numpy as np

from bejeweled_player.board import FLAME_GEM_BASE
from bejeweled_player.config import AppConfig
from bejeweled_player.domain import Frame
from bejeweled_player.interfaces import BoardGeometry
from bejeweled_player.turn import (
    _board_changed_after_move,
    _boards_equivalent_for_noop,
    _boards_equivalent_for_settlement,
    _write_settlement_debug,
    foreground_change_fraction,
)


def _config() -> AppConfig:
    return AppConfig(
        schema_version=1,
        device_serial="test:1",
        screenshot_width=20,
        screenshot_height=20,
        capture_timeout_seconds=1,
        capture_retries=0,
        geometry=BoardGeometry(8, 8, 0, 0, 8, 8),
        recognizer_profile="test",
        rule_set="test",
        random_seed=1,
        planning_budget_seconds=1,
        swipe_duration_ms=120,
        frame_retention="none",
        progress_region=(0, 8, 20, 10),
        progress_full_threshold=0.8,
        foreground_region=(10, 10, 20, 20),
        foreground_change_threshold=0.08,
    )


def _png(image: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()


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


def test_move_change_accepts_special_ordinary_swap() -> None:
    before = np.array([[FLAME_GEM_BASE + 2, 3], [1, 2]])
    current = np.array([[3, FLAME_GEM_BASE + 2], [1, 2]])
    assert _board_changed_after_move(before, current)


def test_noop_equivalence_allows_one_animated_gem() -> None:
    before = np.array([[0, 1], [2, 3]])
    current = np.array([[4, 1], [2, 3]])
    assert _boards_equivalent_for_noop(before, current)


def test_noop_equivalence_rejects_two_changed_gems() -> None:
    before = np.array([[0, 1], [2, 3]])
    current = np.array([[4, 5], [2, 3]])
    assert not _boards_equivalent_for_noop(before, current)


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


def test_foreground_anchor_ignores_board_changes() -> None:
    previous = np.zeros((20, 20), dtype=np.uint8)
    current = previous.copy()
    current[:8, :8] = 255
    assert foreground_change_fraction(_png(previous), _png(current), _config()) == 0


def test_foreground_anchor_rejects_screen_transition() -> None:
    previous = np.zeros((20, 20), dtype=np.uint8)
    current = previous.copy()
    current[10:, 10:] = 255
    assert foreground_change_fraction(_png(previous), _png(current), _config()) > 0.08


def test_settlement_debug_writes_only_the_last_five_frames(tmp_path: Path) -> None:
    frames: deque[tuple[Frame, dict[str, object]]] = deque(
        (
            (
                Frame(
                    str(index),
                    float(index),
                    _png(np.full((20, 20), index, np.uint8)),
                    20,
                    20,
                ),
                {},
            )
            for index in range(7)
        ),
        maxlen=5,
    )

    _write_settlement_debug(tmp_path, frames, ValueError("changed"))

    assert len(list(tmp_path.glob("*.png"))) == 5
    summary = (tmp_path / "summary.json").read_text()
    assert '"last_error": "changed"' in summary
    assert '"path"' in summary
