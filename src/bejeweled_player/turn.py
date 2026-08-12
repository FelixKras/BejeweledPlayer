from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from .adb import AdbActionSink, AdbFrameSource
from .board import Move as ScoredMove
from .board import find_best_move, matched_cells, recognize_board
from .config import AppConfig
from .domain import Coordinate, Move
from .vision import render_grid_overlay


GEM_SYMBOLS = ("R", "G", "B", "Y", "P", "O", "W", "S")


def board_text(board: np.ndarray) -> str:
    return "\n".join(" ".join(GEM_SYMBOLS[int(cell)] for cell in row) for row in board)


def progress_fraction(png: bytes, config: AppConfig) -> float:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("captured frame is not a valid PNG")
    left, top, right, bottom = config.progress_region
    hsv = cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2HSV)
    blue = ((hsv[:, :, 0] >= 85) & (hsv[:, :, 0] <= 135) & (hsv[:, :, 1] >= 60))
    columns = np.count_nonzero(blue, axis=0)
    return float(np.mean(columns > max(2, (bottom - top) // 10)))


def decide_turn(png: bytes, config: AppConfig) -> tuple[np.ndarray, ScoredMove | None]:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("captured frame is not a valid PNG")
    geometry = config.geometry
    board = recognize_board(
        image,
        (geometry.left, geometry.top, geometry.right, geometry.bottom),
        geometry.rows,
        geometry.columns,
        7,
    )
    non_white = int(np.count_nonzero(board != 6))
    unique_gems = len(np.unique(board))
    if non_white < board.size // 2 or unique_gems < 5:
        raise ValueError(
            f"board appearance validation failed: {non_white}/64 colored cells, "
            f"{unique_gems} gem classes"
        )
    return board, find_best_move(board)


def run_turn(
    config: AppConfig,
    output_root: Path,
    execute: bool,
    settle_seconds: float = 0.05,
    settle_timeout_seconds: float = 25.0,
    poll_seconds: float = 0.08,
) -> tuple[ScoredMove | None, str | None, Path]:
    source = AdbFrameSource(
        config.device_serial,
        (config.screenshot_width, config.screenshot_height),
        config.capture_timeout_seconds,
        config.capture_retries,
    )
    before = source.capture()
    session = output_root / datetime.now(UTC).strftime("turn-%Y%m%dT%H%M%S.%fZ")
    session.mkdir(parents=True, exist_ok=False)
    (session / "before.png").write_bytes(before.png)
    render_grid_overlay(before.png, config.geometry, session / "before.overlay.png")
    board, selected = decide_turn(before.png, config)
    action_id = None

    if selected is not None and execute:
        move = Move(Coordinate(*selected.start), Coordinate(*selected.end))
        action_id = AdbActionSink(
            config.device_serial,
            config.swipe_duration_ms,
            config.capture_timeout_seconds,
        ).swipe(move, config.geometry)
        after = _capture_settled(
            source,
            config,
            settle_seconds,
            settle_timeout_seconds,
            poll_seconds,
        )
        (session / "after.png").write_bytes(after.png)
        render_grid_overlay(after.png, config.geometry, session / "after.overlay.png")

    record = {
        "mode": "execute" if execute else "dry-run",
        "board": board.tolist(),
        "board_symbols": board_text(board),
        "selected_move": asdict(selected) if selected else None,
        "action_id": action_id,
        "pre_frame_id": before.frame_id,
    }
    (session / "decision.json").write_text(json.dumps(record, indent=2) + "\n")
    return selected, action_id, session


def _capture_settled(
    source: AdbFrameSource,
    config: AppConfig,
    minimum_wait: float,
    timeout: float,
    poll_seconds: float,
):
    time.sleep(minimum_wait)
    deadline = time.monotonic() + timeout
    previous: np.ndarray | None = None
    last_error: ValueError | None = None
    transition_started = False
    while time.monotonic() < deadline:
        frame = source.capture()
        progress = progress_fraction(frame.png, config)
        if progress >= config.progress_full_threshold:
            transition_started = True
            previous = None
            time.sleep(poll_seconds)
            continue
        if transition_started:
            # The bar reset is the first reliable signal that the level transition ended.
            transition_started = False
            previous = None
        try:
            board, _ = decide_turn(frame.png, config)
        except ValueError as error:
            last_error = error
            time.sleep(poll_seconds)
            continue
        if previous is not None and _boards_equivalent_for_settlement(previous, board):
            return frame
        previous = board
        time.sleep(poll_seconds)
    raise RuntimeError(f"board did not settle within {timeout:g}s: {last_error or 'changed'}")


def _boards_equivalent_for_settlement(previous: np.ndarray, current: np.ndarray) -> bool:
    if previous.shape != current.shape:
        return False
    differing = previous != current
    difference_count = int(np.count_nonzero(differing))
    if difference_count == 0:
        return True
    special_or_unknown = (previous >= 7) | (current >= 7)
    if int(np.count_nonzero(differing & ~special_or_unknown)) == 0:
        return True
    # Animated effects can perturb one ordinary sampled cell without changing playability.
    return difference_count <= 1


def run_multi_turn(
    config: AppConfig,
    output_root: Path,
    turns: int,
    settle_seconds: float = 0.05,
    settle_timeout_seconds: float = 25.0,
    poll_seconds: float = 0.08,
) -> tuple[Path, list[dict[str, object]]]:
    session = output_root / datetime.now(UTC).strftime("multi-%Y%m%dT%H%M%S.%fZ")
    session.mkdir(parents=True, exist_ok=False)
    summary_path = session / "summary.json"
    records: list[dict[str, object]] = []

    for index in range(1, turns + 1):
        started = time.monotonic()
        try:
            selected, action_id, turn_session = run_turn(
                config,
                session,
                True,
                settle_seconds,
                settle_timeout_seconds,
                poll_seconds,
            )
            if selected is None:
                raise RuntimeError("no immediate scoring move found")
            records.append(
                {
                    "turn": index,
                    "status": "completed",
                    "move": asdict(selected),
                    "action_id": action_id,
                    "evidence": turn_session.name,
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
        except Exception as error:
            records.append(
                {
                    "turn": index,
                    "status": "failed",
                    "error": str(error),
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
            summary_path.write_text(json.dumps(records, indent=2) + "\n")
            raise
        summary_path.write_text(json.dumps(records, indent=2) + "\n")
    return session, records


def run_unbounded(
    config: AppConfig,
    output_root: Path,
    settle_seconds: float = 0.05,
    settle_timeout_seconds: float = 25.0,
    poll_seconds: float = 0.08,
) -> tuple[Path, list[dict[str, object]]]:
    session = output_root / datetime.now(UTC).strftime("play-%Y%m%dT%H%M%S.%fZ")
    session.mkdir(parents=True, exist_ok=False)
    summary_path = session / "summary.json"
    records: list[dict[str, object]] = []
    turn_number = 0
    try:
        while True:
            turn_number += 1
            started = time.monotonic()
            try:
                selected, action_id, turn_session = run_turn(
                    config,
                    session,
                    True,
                    settle_seconds,
                    settle_timeout_seconds,
                    poll_seconds,
                )
                if selected is None:
                    raise RuntimeError("no immediate scoring move found")
                records.append(
                    {
                        "turn": turn_number,
                        "status": "completed",
                        "move": asdict(selected),
                        "action_id": action_id,
                        "evidence": turn_session.name,
                        "duration_seconds": round(time.monotonic() - started, 3),
                    }
                )
            except Exception as error:
                records.append(
                    {
                        "turn": turn_number,
                        "status": "failed",
                        "error": str(error),
                        "duration_seconds": round(time.monotonic() - started, 3),
                    }
                )
                summary_path.write_text(json.dumps(records, indent=2) + "\n")
                raise
            summary_path.write_text(json.dumps(records, indent=2) + "\n")
    except KeyboardInterrupt:
        records.append({"turn": turn_number, "status": "stopped", "reason": "keyboard interrupt"})
        summary_path.write_text(json.dumps(records, indent=2) + "\n")
    return session, records
