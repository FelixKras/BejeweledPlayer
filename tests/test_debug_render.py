from pathlib import Path

import cv2
import numpy as np

from bejeweled_player.interfaces import BoardGeometry
from bejeweled_player.vision import render_grid_overlay


def test_overlay_renders_configured_grid(tmp_path: Path) -> None:
    success, encoded = cv2.imencode(".png", np.zeros((1536, 720, 3), dtype=np.uint8))
    assert success
    output = tmp_path / "overlay.png"
    render_grid_overlay(encoded.tobytes(), BoardGeometry(8, 8, 0, 320, 720, 1005), output)
    rendered = cv2.imread(str(output))
    assert rendered is not None
    assert rendered[320, 0].tolist() == [0, 255, 255]
