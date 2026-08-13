import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from bejeweled_player.board import (
    UNKNOWN_GEM,
    classify_hue_histogram,
    find_best_move,
    recognize_board,
)
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


def _solid_hsv(hue: int, saturation: int, value: int, size: int = 120) -> np.ndarray:
    hsv = np.full((size, size, 3), (hue, saturation, value), dtype=np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


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
    assert recognized[0, 0] == 8


def test_special_gem_reference_board_recognizes_hypercube_and_flame_identities() -> None:
    fixture = Path(__file__).parents[1] / "datasets/vision-20/special-gems-level3.jpg"
    image = cv2.imread(str(fixture))
    assert image is not None
    recognized = recognize_board(image, (0, 270, 574, 846), 8, 8, 7)
    expected = np.array(
        [
            [0, 0, 3, 6, 6, 3, 4, 1],
            [0, 1, 2, 6, 2, 0, 2, 3],
            [5, 5, 3, 1, 4, 2, 2, 1],
            [6, 4, 3, 2, 0, 4, 5, 1],
            [0, 1, 2, 6, 1, 4, 0, 3],
            [1, 2, 1, 6, 3, 0, 7, 6],
            [2, 2, 0, 5, 6, 0, 2, 5],
            [3, 6, 4, 0, 4, 3, 3, 1],
        ]
    )
    assert np.array_equal(recognized, expected)
    assert recognized[1, 5] == 0  # red with flame effect
    assert recognized[3, 0] == 6  # white with flame effect
    assert recognized[7, 3] == 0  # red with flame effect


def test_labeled_warm_color_cubes_are_not_hypercubes() -> None:
    dataset = Path(__file__).parents[1] / "datasets/vision-20"
    labels = json.loads((dataset / "labels.json").read_text())
    checked = 0
    for record in labels:
        if record["label"] not in {"red", "orange", "yellow"}:
            continue
        image = cv2.imread(str(dataset / "cells" / f"{record['id']}.png"))
        assert image is not None
        recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
        assert recognized[0, 0] != 7, record["id"]
        checked += 1
    assert checked == 551


def test_four_real_hypercube_rotation_phases_are_recognized() -> None:
    fixture = Path(__file__).parents[1] / "datasets/vision-20/hypercube-phases.jpg"
    image = cv2.imread(str(fixture))
    assert image is not None
    recognized = recognize_board(image, (344, 27, 998, 685), 8, 8, 7)
    assert set(map(tuple, np.argwhere(recognized == 7))) == {
        (3, 3),
        (4, 3),
        (4, 5),
        (5, 3),
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


def test_recognizer_distinguishes_dim_shining_green_special() -> None:
    hsv = np.full((100, 100, 3), (60, 140, 170), dtype=np.uint8)
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    recognized = recognize_board(image, (0, 0, 100, 100), 1, 1, 7)
    assert recognized[0, 0] == 8


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
