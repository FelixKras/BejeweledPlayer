from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent / "vision-20"
CLASSES = ("yellow", "orange", "red")


def main() -> None:
    labels = json.loads((ROOT / "labels.json").read_text())
    samples: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {name: [] for name in CLASSES}
    for record in labels:
        label = record["label"]
        if label not in samples:
            continue
        image = cv2.imread(str(ROOT / "cells" / f"{record['id']}.png"))
        if image is None:
            raise RuntimeError(f"missing cell {record['id']}")
        size = min(image.shape[:2])
        center_y, center_x = image.shape[0] // 2, image.shape[1] // 2
        radius = size // 4
        body = image[
            center_y - radius : center_y + radius,
            center_x - radius : center_x + radius,
        ]
        samples[label].append((image, body))

    canvas = np.full((1500, 1500, 3), 255, np.uint8)
    cv2.putText(
        canvas,
        "HSV hue histograms: yellow, orange, red cubes",
        (40, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 0),
        2,
    )
    for row, name in enumerate(CLASSES):
        for column, part in enumerate((0, 1)):
            normalized = []
            for pair in samples[name]:
                hsv = cv2.cvtColor(pair[part], cv2.COLOR_BGR2HSV)
                hues = hsv[:, :, 0][hsv[:, :, 1] >= 90]
                histogram = np.histogram(hues, 18, (0, 180))[0].astype(float)
                normalized.append(histogram / max(1, histogram.sum()))
            values = np.array(normalized)
            mean = values.mean(axis=0)
            low = np.percentile(values, 10, axis=0)
            high = np.percentile(values, 90, axis=0)
            origin_x = 70 + column * 730
            baseline = 440 + row * 450
            region = "full cell" if part == 0 else "central body"
            cv2.putText(
                canvas,
                f"{name} - {region} (n={len(values)})",
                (origin_x, baseline - 315),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                (0, 0, 0),
                2,
            )
            for index, value in enumerate(mean):
                bar_width = 36
                x = origin_x + index * bar_width
                height = round(value * 900)
                low_height = round(low[index] * 900)
                high_height = round(high[index] * 900)
                color = cv2.cvtColor(
                    np.uint8([[[index * 10 + 5, 230, 230]]]), cv2.COLOR_HSV2BGR
                )[0, 0].tolist()
                cv2.rectangle(
                    canvas,
                    (x, baseline - height),
                    (x + bar_width - 5, baseline),
                    color,
                    -1,
                )
                cv2.line(
                    canvas,
                    (x + bar_width // 2, baseline - low_height),
                    (x + bar_width // 2, baseline - high_height),
                    (0, 0, 0),
                    2,
                )
                cv2.putText(
                    canvas,
                    str(index * 10),
                    (x, baseline + 18),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.28,
                    (0, 0, 0),
                    1,
                )
            cv2.putText(
                canvas,
                "bar=mean; line=10th-90th percentile",
                (origin_x + 120, baseline + 52),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 0, 0),
                1,
            )
    cv2.imwrite(str(ROOT / "yellow-orange-red-histograms.png"), canvas)
    print({name: len(values) for name, values in samples.items()})


if __name__ == "__main__":
    main()
