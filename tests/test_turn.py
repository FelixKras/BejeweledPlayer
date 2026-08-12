import cv2
import numpy as np
import pytest

from bejeweled_player.board import find_best_move, recognize_board
from bejeweled_player.config import AppConfig
from bejeweled_player.interfaces import BoardGeometry
from bejeweled_player.turn import decide_turn

COLORS = {
    0: (0, 0, 255),
    1: (0, 255, 0),
    2: (255, 0, 0),
    3: (0, 255, 255),
    4: (255, 0, 255),
    5: (0, 128, 255),
    6: (220, 220, 220),
}


def test_recognizer_and_immediate_decision_on_synthetic_board() -> None:
    values = np.array(
        [
            [1, 2, 1, 4],
            [3, 1, 5, 6],
            [2, 3, 4, 5],
            [4, 5, 6, 2],
        ]
    )
    image = np.zeros((400, 400, 3), dtype=np.uint8)
    for row in range(4):
        for column in range(4):
            image[row * 100 : (row + 1) * 100, column * 100 : (column + 1) * 100] = (
                COLORS[int(values[row, column])]
            )
    recognized = recognize_board(image, (0, 0, 400, 400), 4, 4, 7)
    assert np.array_equal(recognized, values)
    move = find_best_move(recognized)
    assert move is not None
    assert {move.start, move.end} == {(0, 1), (1, 1)}


def test_turn_rejects_unrelated_low_color_screen() -> None:
    success, png = cv2.imencode(".png", np.full((1536, 720, 3), 240, dtype=np.uint8))
    assert success
    config = AppConfig(
        schema_version=1,
        device_serial="test:1",
        screenshot_width=720,
        screenshot_height=1536,
        capture_timeout_seconds=1,
        capture_retries=0,
        geometry=BoardGeometry(8, 8, 0, 320, 720, 1005),
        recognizer_profile="test",
        rule_set="test",
        random_seed=1,
        planning_budget_seconds=1,
        swipe_duration_ms=120,
        frame_retention="none",
        progress_region=(20, 1015, 700, 1065),
        progress_full_threshold=0.8,
    )
    with pytest.raises(ValueError, match="appearance validation failed"):
        decide_turn(png.tobytes(), config)


def test_turn_allows_in_game_board_with_existing_symbolic_match() -> None:
    values = np.array(
        [
            [0, 0, 0, 2],
            [1, 2, 3, 4],
            [2, 1, 4, 5],
            [3, 4, 5, 6],
        ]
    )
    image = np.zeros((400, 400, 3), dtype=np.uint8)
    for row in range(4):
        for column in range(4):
            image[row * 100 : (row + 1) * 100, column * 100 : (column + 1) * 100] = (
                COLORS[int(values[row, column])]
            )
    success, png = cv2.imencode(".png", image)
    assert success
    config = AppConfig(
        schema_version=1,
        device_serial="test:1",
        screenshot_width=400,
        screenshot_height=800,
        capture_timeout_seconds=1,
        capture_retries=0,
        geometry=BoardGeometry(4, 4, 0, 0, 400, 400),
        recognizer_profile="test",
        rule_set="test",
        random_seed=1,
        planning_budget_seconds=1,
        swipe_duration_ms=120,
        frame_retention="none",
        progress_region=(0, 410, 400, 430),
        progress_full_threshold=0.8,
    )
    board, _ = decide_turn(png.tobytes(), config)
    assert np.array_equal(board, values)
