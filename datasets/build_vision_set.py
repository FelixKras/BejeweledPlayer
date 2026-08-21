from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "datasets" / "vision-20"
SOURCES = (
    "sessions/turn-20260812T194929.451558Z/before.png",
    "sessions/play-20260812T194300.493278Z/turn-20260812T194331.076534Z/before.png",
    "sessions/play-20260813T042854.732756Z/turn-20260813T042859.083981Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T203745.757821Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T210724.255753Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T213315.074574Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T215855.904130Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T222426.454510Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T225010.346738Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T231529.753929Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260812T234055.056845Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T000605.239528Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T003059.423945Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T005607.079297Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T012104.807548Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T014605.893666Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T021137.890068Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T023650.849777Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T030214.428862Z/before.png",
    "sessions/play-20260812T203742.274360Z/turn-20260813T032748.513588Z/before.png",
)


def main() -> None:
    cells_dir = OUTPUT / "cells"
    sheets_dir = OUTPUT / "sheets"
    cells_dir.mkdir(parents=True, exist_ok=True)
    sheets_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    board_tiles: list[np.ndarray] = []

    for board_index, relative in enumerate(SOURCES, 1):
        image = cv2.imread(str(ROOT / relative))
        if image is None:
            raise RuntimeError(f"could not read {relative}")
        board = image[448:1408, 0:960]
        annotated = board.copy()
        for row in range(8):
            for column in range(8):
                top, left = row * 120, column * 120
                cell = board[top : top + 120, left : left + 120]
                cell_id = f"b{board_index:02d}-r{row + 1}-c{column + 1}"
                cv2.imwrite(str(cells_dir / f"{cell_id}.png"), cell)
                records.append(
                    {
                        "id": cell_id,
                        "board": board_index,
                        "row": row + 1,
                        "column": column + 1,
                        "source": relative,
                        "label": "uncertain",
                        "confidence": 0.0,
                        "review_required": True,
                    }
                )
                cv2.putText(
                    annotated,
                    f"{row + 1},{column + 1}",
                    (left + 4, top + 16),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (0, 0, 0),
                    3,
                )
                cv2.putText(
                    annotated,
                    f"{row + 1},{column + 1}",
                    (left + 4, top + 16),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (255, 255, 255),
                    1,
                )
        tile = cv2.resize(annotated, (480, 480), interpolation=cv2.INTER_AREA)
        cv2.putText(
            tile, f"Board {board_index}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3
        )
        cv2.putText(
            tile, f"Board {board_index}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1
        )
        board_tiles.append(tile)

    for sheet_index in range(4):
        tiles = board_tiles[sheet_index * 5 : (sheet_index + 1) * 5]
        sheet = np.hstack(tiles)
        cv2.imwrite(
            str(sheets_dir / f"boards-{sheet_index * 5 + 1:02d}-{sheet_index * 5 + 5:02d}.png"),
            sheet,
        )

    (OUTPUT / "labels.json").write_text(json.dumps(records, indent=2) + "\n")
    (OUTPUT / "sources.json").write_text(json.dumps(SOURCES, indent=2) + "\n")


if __name__ == "__main__":
    main()
