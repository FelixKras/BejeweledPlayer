from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ..domain import Coordinate
from ..interfaces import BoardGeometry


def render_grid_overlay(png: bytes, geometry: BoardGeometry, output: Path) -> None:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("input is not a valid PNG image")
    height, width = image.shape[:2]
    if not (0 <= geometry.left < geometry.right <= width):
        raise ValueError("horizontal board geometry is outside the frame")
    if not (0 <= geometry.top < geometry.bottom <= height):
        raise ValueError("vertical board geometry is outside the frame")

    color = (0, 255, 255)
    for column in range(geometry.columns + 1):
        x = round(geometry.left + column * geometry.width / geometry.columns)
        cv2.line(image, (x, geometry.top), (x, geometry.bottom), color, 1)
    for row in range(geometry.rows + 1):
        y = round(geometry.top + row * geometry.height / geometry.rows)
        cv2.line(image, (geometry.left, y), (geometry.right, y), color, 1)
    for row in range(geometry.rows):
        for column in range(geometry.columns):
            center = geometry.center(Coordinate(row, column))
            cv2.putText(
                image,
                f"{row},{column}",
                (center[0] - 18, center[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                color,
                1,
                cv2.LINE_AA,
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), image):
        raise OSError(f"failed to write debug image: {output}")
