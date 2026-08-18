from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).parent / "vision-20"
OUTPUT = ROOT / "gem-histogram-infographic.png"
CLASSES = ("red", "orange", "yellow", "green", "blue", "purple")


def main() -> None:
    labels = json.loads((ROOT / "labels.json").read_text())
    examples = {}
    for record in labels:
        name = record["label"]
        if name in CLASSES and name not in examples and record["confidence"] >= 0.95:
            examples[name] = ROOT / "cells" / f"{record['id']}.png"

    canvas = np.full((1220, 1680, 3), (22, 20, 28), np.uint8)
    cv2.putText(canvas, "THE COLOR SIGNATURES OF BEJEWELED", (64, 78),
                cv2.FONT_HERSHEY_DUPLEX, 1.45, (245, 240, 232), 3, cv2.LINE_AA)
    cv2.putText(canvas, "Real gem crops + saturation-filtered HSV hue histograms", (67, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (180, 170, 190), 2, cv2.LINE_AA)

    for index, name in enumerate(CLASSES):
        row, column = divmod(index, 3)
        x0, y0 = 55 + column * 545, 165 + row * 500
        cv2.rectangle(canvas, (x0, y0), (x0 + 510, y0 + 455), (39, 35, 48), -1)
        cv2.rectangle(canvas, (x0, y0), (x0 + 510, y0 + 455), (72, 63, 84), 2)

        image = cv2.imread(str(examples[name]))
        if image is None:
            raise RuntimeError(f"missing example for {name}")
        gem = cv2.resize(image, (190, 190), interpolation=cv2.INTER_CUBIC)
        canvas[y0 + 55:y0 + 245, x0 + 24:x0 + 214] = gem
        cv2.putText(canvas, name.upper(), (x0 + 25, y0 + 38),
                    cv2.FONT_HERSHEY_DUPLEX, 0.82, (245, 240, 232), 2, cv2.LINE_AA)

        size = min(image.shape[:2])
        cy, cx = image.shape[0] // 2, image.shape[1] // 2
        radius = size // 4
        body = image[cy - radius:cy + radius, cx - radius:cx + radius]
        hsv = cv2.cvtColor(body, cv2.COLOR_BGR2HSV)
        hues = hsv[:, :, 0][hsv[:, :, 1] >= 90]
        histogram = np.histogram(hues, 18, (0, 180))[0].astype(float)
        histogram /= max(1, histogram.max())

        chart_x, baseline = x0 + 235, y0 + 270
        for bin_index, value in enumerate(histogram):
            bar_width = 14
            x = chart_x + bin_index * bar_width
            bar_height = round(value * 175)
            color = cv2.cvtColor(
                np.uint8([[[bin_index * 10 + 5, 225, 235]]]), cv2.COLOR_HSV2BGR
            )[0, 0].tolist()
            cv2.rectangle(canvas, (x, baseline - bar_height),
                          (x + bar_width - 2, baseline), color, -1)
        cv2.line(canvas, (chart_x, baseline), (chart_x + 252, baseline), (145, 135, 155), 1)
        cv2.putText(canvas, "0", (chart_x, baseline + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 150, 170), 1, cv2.LINE_AA)
        cv2.putText(canvas, "HUE", (chart_x + 101, baseline + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 150, 170), 1, cv2.LINE_AA)
        cv2.putText(canvas, "180", (chart_x + 225, baseline + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 150, 170), 1, cv2.LINE_AA)

        cv2.putText(canvas, "Facet highlights create secondary peaks.", (x0 + 25, y0 + 338),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (205, 195, 210), 1, cv2.LINE_AA)
        cv2.putText(canvas, "The dominant hue family remains the clue.", (x0 + 25, y0 + 372),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (205, 195, 210), 1, cv2.LINE_AA)

    cv2.putText(canvas, "VISION PIPELINE  /  CENTER BODY  /  SATURATION >= 90  /  18 HUE BINS",
                (65, 1180), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (140, 130, 150), 2, cv2.LINE_AA)
    if not cv2.imwrite(str(OUTPUT), canvas):
        raise RuntimeError(f"failed to write {OUTPUT}")
    print(OUTPUT)


if __name__ == "__main__":
    main()
