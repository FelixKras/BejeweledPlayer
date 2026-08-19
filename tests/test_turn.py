import cv2
import numpy as np
import pytest

from bejeweled_player.board import (
    UNKNOWN_GEM,
    classify_hue_histogram,
    classify_unknown_gem,
    find_best_move,
    recognize_board,
)
from bejeweled_player.config import AppConfig
from bejeweled_player.interfaces import BoardGeometry
from bejeweled_player.turn import _recognize_frame, continue_button, decide_turn

COLORS = {
    0: (0, 0, 255),
    1: (0, 255, 0),
    2: (255, 0, 0),
    3: (0, 255, 255),
    4: (255, 0, 255),
    5: (0, 128, 255),
    6: (220, 220, 220),
}


def _solid_hsv(hue: int, saturation: int, value: int, size: int = 120) -> np.ndarray:
    hsv = np.full((size, size, 3), (hue, saturation, value), dtype=np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def test_continue_button_detects_result_panel_and_green_pill() -> None:
    hsv = np.zeros((1280, 574, 3), dtype=np.uint8)
    hsv[500:1230] = (15, 150, 220)
    cv2.rectangle(hsv, (140, 960), (440, 1045), (65, 220, 160), -1)
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    success, png = cv2.imencode(".png", image)
    assert success
    assert continue_button(png.tobytes()) == (290, 1003)


def test_continue_button_rejects_green_board_without_result_panel() -> None:
    image = np.full((1280, 574, 3), (0, 180, 0), dtype=np.uint8)
    success, png = cv2.imencode(".png", image)
    assert success
    assert continue_button(png.tobytes()) is None


ORDINARY_GEM_CASES = [
    pytest.param(label, hue, saturation, value, id=f"label-{label}-h{hue}-s{saturation}-v{value}")
    for label, variants in {
        0: ((0, 255, 255), (2, 190, 210), (175, 230, 180), (178, 140, 240)),
        1: ((45, 255, 255), (55, 180, 210), (65, 230, 180), (75, 140, 240)),
        2: ((92, 255, 255), (102, 180, 210), (112, 230, 180), (122, 140, 240)),
        3: ((30, 255, 255), (32, 180, 210), (34, 230, 180), (36, 140, 240)),
        4: ((132, 255, 255), (142, 180, 210), (152, 230, 180), (162, 140, 240)),
        5: ((10, 255, 255), (13, 180, 210), (16, 230, 180), (19, 140, 240)),
    }.items()
    for hue, saturation, value in variants
]


@pytest.mark.parametrize(("label", "hue", "saturation", "value"), ORDINARY_GEM_CASES)
def test_recognizer_classifies_ordinary_gem_variants(
    label: int, hue: int, saturation: int, value: int
) -> None:
    image = _solid_hsv(hue, saturation, value)
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == label


@pytest.mark.parametrize(
    ("hue", "saturation", "value"),
    [
        pytest.param(0, 0, 245, id="neutral-bright"),
        pytest.param(20, 20, 220, id="warm-tint"),
        pytest.param(105, 35, 190, id="cool-tint"),
        pytest.param(150, 60, 235, id="purple-tint"),
    ],
)
def test_recognizer_classifies_white_gem_variants(
    hue: int, saturation: int, value: int
) -> None:
    image = _solid_hsv(hue, saturation, value)
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == 6


@pytest.mark.parametrize(
    ("purple_start", "purple_end"),
    [
        pytest.param(30, 54, id="purple-left"),
        pytest.param(42, 66, id="purple-center-left"),
        pytest.param(54, 78, id="purple-center-right"),
        pytest.param(66, 90, id="purple-right"),
    ],
)
def test_recognizer_classifies_hypercube_variants(
    purple_start: int, purple_end: int
) -> None:
    image = _solid_hsv(20, 220, 220)
    image[:, purple_start:purple_end] = _solid_hsv(150, 220, 220)[:, : purple_end - purple_start]
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == 7


@pytest.mark.parametrize(
    ("hue", "saturation", "value"),
    [
        pytest.param(45, 120, 150, id="dim-yellow-green"),
        pytest.param(55, 140, 170, id="dim-green"),
        pytest.param(65, 155, 180, id="muted-green"),
        pytest.param(75, 100, 140, id="dim-blue-green"),
    ],
)
def test_recognizer_classifies_shining_green_special_variants(
    hue: int, saturation: int, value: int
) -> None:
    image = _solid_hsv(hue, saturation, value)
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == 18


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


def test_recognizer_uses_separated_hue_histogram_for_hypercube() -> None:
    image = _solid_hsv(20, 220, 220, 100)
    image[:, 48:72] = _solid_hsv(150, 220, 220, 100)[:, :24]
    recognized = recognize_board(image, (0, 0, 100, 100), 1, 1, 7)
    assert recognized[0, 0] == 7


def test_recognizer_keeps_two_family_faceted_purple_ordinary() -> None:
    image = np.full((100, 100, 3), COLORS[4], dtype=np.uint8)
    image[:, :20] = COLORS[2]
    recognized = recognize_board(image, (0, 0, 100, 100), 1, 1, 7)
    assert recognized[0, 0] == 4


def test_recognizer_ignores_multicolor_cell_edges() -> None:
    image = np.full((120, 120, 3), COLORS[0], dtype=np.uint8)
    image[30:90, 30:90] = COLORS[3]
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == 3


def test_histogram_template_rejects_ambiguous_color() -> None:
    histogram = np.zeros(18, dtype=np.int64)
    histogram[3] = 100
    histogram[6] = 100
    assert classify_hue_histogram(histogram) == UNKNOWN_GEM


def test_unknown_fallback_recovers_gem_under_bright_effect() -> None:
    patch = _solid_hsv(150, 220, 220, 120)
    cv2.line(patch, (0, 70), (119, 40), (255, 255, 255), 22)
    cv2.circle(patch, (60, 60), 22, (255, 255, 255), 8)
    assert classify_unknown_gem(patch) == 4


def test_unknown_fallback_rejects_balanced_competing_colors() -> None:
    patch = _solid_hsv(3, 220, 220, 120)
    patch[:, 60:] = _solid_hsv(105, 220, 220, 120)[:, 60:]
    assert classify_unknown_gem(patch) == UNKNOWN_GEM


def test_recognizer_distinguishes_dim_shining_green_special() -> None:
    hsv = np.full((100, 100, 3), (60, 140, 170), dtype=np.uint8)
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    recognized = recognize_board(image, (0, 0, 100, 100), 1, 1, 7)
    assert recognized[0, 0] == 18


def test_recognizer_keeps_rendered_green_as_ordinary() -> None:
    hsv = np.full((100, 100, 3), (60, 200, 200), dtype=np.uint8)
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    recognized = recognize_board(image, (0, 0, 100, 100), 1, 1, 7)
    assert recognized[0, 0] == 1


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


def test_settlement_recognition_can_preserve_one_unknown_cell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = np.tile(np.arange(8) % 7, (8, 1))
    image = np.zeros((800, 800, 3), dtype=np.uint8)
    for row in range(8):
        for column in range(8):
            image[row * 100 : (row + 1) * 100, column * 100 : (column + 1) * 100] = (
                COLORS[int(values[row, column])]
            )
    success, png = cv2.imencode(".png", image)
    assert success
    config = AppConfig(
        schema_version=1,
        device_serial="test:1",
        screenshot_width=800,
        screenshot_height=900,
        capture_timeout_seconds=1,
        capture_retries=0,
        geometry=BoardGeometry(8, 8, 0, 0, 800, 800),
        recognizer_profile="test",
        rule_set="test",
        random_seed=1,
        planning_budget_seconds=1,
        swipe_duration_ms=120,
        frame_retention="none",
        progress_region=(0, 810, 800, 830),
        progress_full_threshold=0.8,
    )
    recognized = values.astype(np.int8)
    recognized[3, 4] = UNKNOWN_GEM
    monkeypatch.setattr("bejeweled_player.turn.recognize_board", lambda *args: recognized)
    board = _recognize_frame(png.tobytes(), config, max_unknown=1)
    assert board[3, 4] == UNKNOWN_GEM
    with pytest.raises(ValueError, match="1/64 unknown cells"):
        decide_turn(png.tobytes(), config)
