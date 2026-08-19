import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from bejeweled_player.board import (
    FLAME_GEM_BASE,
    HYPERCUBE,
    gem_color,
    recognize_board,
)

DATASET = Path(__file__).parents[1] / "datasets/vision-20"
COLOR_LABELS = {
    "red": 0,
    "green": 1,
    "blue": 2,
    "yellow": 3,
    "purple": 4,
    "orange": 5,
    "white": 6,
    "hypercube": HYPERCUBE,
}
LABELED_GEMS = json.loads((DATASET / "labels.json").read_text())


@pytest.mark.parametrize("record", LABELED_GEMS, ids=lambda record: record["id"])
def test_all_labeled_gem_identities(record: dict[str, object]) -> None:
    image = cv2.imread(str(DATASET / "cells" / f"{record['id']}.png"))
    assert image is not None

    label = int(recognize_board(image, (0, 0, 120, 120), 1, 1, 7)[0, 0])

    assert gem_color(label) == COLOR_LABELS[record["label"]]


def test_labeled_special_board_matches_identity_and_effect_metadata() -> None:
    metadata = json.loads((DATASET / "special-gems-level3.json").read_text())
    image = cv2.imread(str(DATASET / metadata["image"]))
    assert image is not None
    recognized = recognize_board(image, tuple(metadata["geometry"]), 8, 8, 7)
    expected = np.asarray(
        [[COLOR_LABELS[identity] for identity in row] for row in metadata["identities"]],
        dtype=np.int8,
    )
    for coordinate, effect in metadata["effects"].items():
        row, column = (int(value) - 1 for value in coordinate[1:].split("c"))
        if effect == "flame":
            expected[row, column] += FLAME_GEM_BASE
        elif effect == "hypercube":
            expected[row, column] = HYPERCUBE
        else:
            raise AssertionError(f"unsupported labeled effect: {effect}")

    assert np.array_equal(recognized, expected)


def test_labeled_hypercube_rotation_phases() -> None:
    image = cv2.imread(str(DATASET / "hypercube-phases.jpg"))
    assert image is not None
    recognized = recognize_board(image, (344, 27, 998, 685), 8, 8, 7)
    assert set(map(tuple, np.argwhere(recognized == HYPERCUBE))) == {
        (3, 3),
        (4, 3),
        (4, 5),
        (5, 3),
    }


def test_dark_red_hypercube_rotation_phase() -> None:
    image = cv2.imread(str(DATASET / "hypercube-dark-red-phase.png"))
    assert image is not None
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] == HYPERCUBE


def test_dark_overlay_white_gem_is_not_a_hypercube() -> None:
    image = cv2.imread(str(DATASET / "white-gem-dark-overlay.png"))
    assert image is not None
    recognized = recognize_board(image, (0, 0, 120, 120), 1, 1, 7)
    assert recognized[0, 0] != HYPERCUBE
