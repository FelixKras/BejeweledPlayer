import json
from pathlib import Path

import cv2
import numpy as np

from bejeweled_player.board import _HUE_TEMPLATE_BINS, gem_color, recognize_board

KNOWN_FAILURES = {
    "turn-20260819T063845.287164Z",
    "turn-20260819T063958.061537Z",
    "turn-20260819T064028.310041Z",
    "turn-20260819T064059.758481Z",
}

COLOR_LABELS = {"red": 0, "green": 1, "blue": 2, "yellow": 3, "purple": 4, "orange": 5, "white": 6}
INV_COLOR_LABELS = {v: k for k, v in COLOR_LABELS.items()}

LLM_DATASET = json.loads(Path("datasets/vision-llm-labeled/consensus_dataset.json").read_text())

for record in LLM_DATASET:
    if record["frame_id"] not in KNOWN_FAILURES:
        continue

    img_path = Path("datasets/vision-llm-labeled") / record["image_path"]
    image = cv2.imread(str(img_path))
    recognized = recognize_board(image, (0, 448, 960, 1408), 8, 8, 7)

    gemini = record["annotations"]["google/gemini-3.7-flash"]
    grok = record["annotations"]["x-ai/grok-4.6"]

    crop = image[448:1408, 0:960]
    rows, cols = 8, 8
    cell_size = min(crop.shape[0] // rows, crop.shape[1] // cols)

    for r in range(8):
        for c in range(8):
            g1 = gemini["identities"][r][c]
            g2 = grok["identities"][r][c]
            if g1 == g2 and g1 != "na" and g1 != "hypercube":
                expected_color_int = COLOR_LABELS[g1]
                actual_label_int = int(recognized[r, c])
                actual_color_int = gem_color(actual_label_int)

                if actual_color_int != expected_color_int:
                    print(f"\nFrame: {record['frame_id']} | Cell: r{r + 1}c{c + 1}")
                    print(f"LLM Consensus : {g1.upper()}")
                    print(
                        f"Recognizer    : {INV_COLOR_LABELS.get(actual_color_int, 'unknown').upper()}"
                    )

                    x = round((c + 0.5) * crop.shape[1] / cols)
                    y = round((r + 0.5) * crop.shape[0] / rows)
                    radius = max(2, cell_size // 8)
                    histogram_radius = max(radius, cell_size // 4)
                    histogram_patch = crop[
                        max(0, y - histogram_radius) : y + histogram_radius,
                        max(0, x - histogram_radius) : x + histogram_radius,
                    ]
                    histogram_hsv = cv2.cvtColor(histogram_patch, cv2.COLOR_BGR2HSV)
                    saturated_hues = histogram_hsv[:, :, 0][histogram_hsv[:, :, 1] >= 90]
                    histogram = np.histogram(saturated_hues, bins=18, range=(0, 180))[0]

                    # Normalize for display
                    hist_display = [int(v) for v in histogram]
                    print(f"Histogram     : {hist_display}")

                    yellow_bins = _HUE_TEMPLATE_BINS[3]
                    orange_bins = _HUE_TEMPLATE_BINS[5]

                    yellow_mass = sum(histogram[b] for b in yellow_bins)
                    orange_mass = sum(histogram[b] for b in orange_bins)
                    print(f"  -> Mass in Yellow bins {yellow_bins}: {yellow_mass}")
                    print(f"  -> Mass in Orange bins {orange_bins}: {orange_mass}")
