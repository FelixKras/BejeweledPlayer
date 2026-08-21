import json
from pathlib import Path

from typing import Any
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
def test_all_labeled_gem_identities(record: dict[str, Any]) -> None:
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


LLM_DATASET = json.loads(
    (DATASET.parent / "vision-llm-labeled" / "consensus_dataset.json").read_text()
)


KNOWN_FAILURES = {
    "turn-20260819T063845.287164Z",
    "turn-20260819T063958.061537Z",
    "turn-20260819T064028.310041Z",
    "turn-20260819T064059.758481Z",
}


@pytest.mark.parametrize("record", LLM_DATASET, ids=lambda r: r["frame_id"])
def test_llm_consensus_board_recognition(record: dict[str, Any]) -> None:
    if record["frame_id"] in KNOWN_FAILURES:
        pytest.xfail("Known yellow/orange hue boundary classification failures")

    image_path = DATASET.parent / "vision-llm-labeled" / record["image_path"]
    image = cv2.imread(str(image_path))
    assert image is not None
    recognized = recognize_board(image, (0, 448, 960, 1408), 8, 8, 7)

    gemini = record["annotations"].get("google/gemini-3.7-flash")
    grok = record["annotations"].get("x-ai/grok-4.6")

    if not gemini or not grok:
        pytest.skip("Missing annotations from one or both models")

    mismatches = []
    for r in range(8):
        for c in range(8):
            g1 = gemini["identities"][r][c]
            g2 = grok["identities"][r][c]
            if g1 == g2 and g1 != "na":
                expected_label = g1
                actual_label = int(recognized[r, c])

                if expected_label == "hypercube":
                    if actual_label != HYPERCUBE:
                        mismatches.append(
                            f"r{r + 1}c{c + 1}: expected hypercube, got {actual_label}"
                        )
                else:
                    expected_color = COLOR_LABELS[expected_label]
                    actual_color = gem_color(actual_label)
                    if actual_color != expected_color:
                        mismatches.append(
                            f"r{r + 1}c{c + 1}: expected {expected_label} ({expected_color}), got {actual_color} (raw {actual_label})"
                        )

    assert not mismatches, f"Recognition failed on {len(mismatches)} cells:\n" + "\n".join(
        mismatches
    )
