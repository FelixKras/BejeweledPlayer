from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from .adb import AdbActionSink, AdbFrameSource
from .board import (
    FLAME_GEM_BASE,
    STAR_GEM_BASE,
    UNKNOWN_GEM,
    find_best_move,
    recognize_board,
)
from .board import Move as ScoredMove
from .config import AppConfig
from .domain import Coordinate, Frame, Move
from .vision import render_grid_overlay

GEM_SYMBOLS = ("R", "G", "B", "Y", "P", "O", "W", "C", "X", "?")


def board_text(board: np.ndarray) -> str:
    def symbol(label: int) -> str:
        if FLAME_GEM_BASE <= label < FLAME_GEM_BASE + 7:
            return f"F{GEM_SYMBOLS[label - FLAME_GEM_BASE]}"
        if STAR_GEM_BASE <= label < STAR_GEM_BASE + 7:
            return f"S{GEM_SYMBOLS[label - STAR_GEM_BASE]}"
        return GEM_SYMBOLS[label]

    return "\n".join(" ".join(symbol(int(cell)) for cell in row) for row in board)


def progress_fraction(png: bytes, config: AppConfig) -> float:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("captured frame is not a valid PNG")
    left, top, right, bottom = config.progress_region
    hsv = cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2HSV)
    blue = ((hsv[:, :, 0] >= 85) & (hsv[:, :, 0] <= 135) & (hsv[:, :, 1] >= 60))
    columns = np.count_nonzero(blue, axis=0)
    return float(np.mean(columns > max(2, (bottom - top) // 10)))


def foreground_change_fraction(previous_png: bytes, current_png: bytes, config: AppConfig) -> float:
    previous = cv2.imdecode(np.frombuffer(previous_png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    current = cv2.imdecode(np.frombuffer(current_png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if previous is None or current is None or previous.shape != current.shape:
        return 1.0
    left, top, right, bottom = config.foreground_region
    difference = cv2.absdiff(previous[top:bottom, left:right], current[top:bottom, left:right])
    return float(np.mean(difference > 20))


def continue_button(png: bytes) -> tuple[int, int] | None:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    panel = hsv[int(height * 0.38) : int(height * 0.96)]
    orange_panel_fraction = float(
        np.mean(
            (panel[:, :, 0] >= 5)
            & (panel[:, :, 0] <= 30)
            & (panel[:, :, 1] >= 55)
            & (panel[:, :, 2] >= 90)
        )
    )
    if orange_panel_fraction < 0.20:
        return None
    green = (
        (hsv[:, :, 0] >= 35)
        & (hsv[:, :, 0] <= 90)
        & (hsv[:, :, 1] >= 90)
        & (hsv[:, :, 2] >= 45)
    ).astype(np.uint8) * 255
    green[: int(height * 0.55)] = 0
    contours, _ = cv2.findContours(green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        x, y, button_width, button_height = cv2.boundingRect(contour)
        if (
            button_width >= width * 0.35
            and button_height >= height * 0.025
            and button_width >= button_height * 2.5
        ):
            return x + button_width // 2, y + button_height // 2
    return None


def decide_turn(png: bytes, config: AppConfig) -> tuple[np.ndarray, ScoredMove | None]:
    board = _recognize_frame(png, config)
    unknown_count = int(np.count_nonzero(board == UNKNOWN_GEM))
    if unknown_count:
        raise ValueError(f"board recognition uncertain: {unknown_count}/64 unknown cells")
    return board, find_best_move(board)


def _recognize_frame(png: bytes, config: AppConfig, max_unknown: int = 0) -> np.ndarray:
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
    unknown_count = int(np.count_nonzero(board == UNKNOWN_GEM))
    if unknown_count > max_unknown:
        raise ValueError(f"board recognition uncertain: {unknown_count}/64 unknown cells")
    if non_white < board.size // 2 or unique_gems < 5:
        raise ValueError(
            f"board appearance validation failed: {non_white}/64 colored cells, "
            f"{unique_gems} gem classes"
        )
    return board


def run_turn(
    config: AppConfig,
    output_root: Path,
    execute: bool,
    settle_seconds: float = 0.05,
    settle_timeout_seconds: float = 120.0,
    poll_seconds: float = 0.08,
) -> tuple[ScoredMove | None, str | None, Path]:
    source = AdbFrameSource(
        config.device_serial,
        (config.screenshot_width, config.screenshot_height),
        config.capture_timeout_seconds,
        config.capture_retries,
    )
    last_error: ValueError | None = None
    sink = AdbActionSink(
        config.device_serial,
        config.swipe_duration_ms,
        config.capture_timeout_seconds,
    )
    for _ in range(12):
        candidate = source.capture()
        button = continue_button(candidate.png)
        if button is not None:
            if not execute:
                raise ValueError("completion screen requires Continue; input remains disabled")
            sink.tap(button)
            time.sleep(1.0)
            continue
        try:
            candidate_board, candidate_move = decide_turn(candidate.png, config)
        except ValueError as error:
            last_error = error
            time.sleep(poll_seconds)
            continue
        if candidate_move is not None:
            before, board, selected = candidate, candidate_board, candidate_move
            break
        time.sleep(poll_seconds)
    else:
        if last_error is not None:
            raise last_error

    session = output_root / datetime.now(UTC).strftime("turn-%Y%m%dT%H%M%S.%fZ")
    session.mkdir(parents=True, exist_ok=False)
    retain_all_frames = config.frame_retention == "all"
    if retain_all_frames:
        (session / "before.png").write_bytes(before.png)
        render_grid_overlay(before.png, config.geometry, session / "before.overlay.png")
    action_id = None

    if selected is not None and execute:
        move = Move(Coordinate(*selected.start), Coordinate(*selected.end))
        action_id = sink.swipe(move, config.geometry)
        try:
            after = _capture_settled(
                source,
                config,
                board,
                settle_seconds,
                settle_timeout_seconds,
                poll_seconds,
            )
        except Exception:
            if config.frame_retention == "errors":
                (session / "before.png").write_bytes(before.png)
                render_grid_overlay(before.png, config.geometry, session / "before.overlay.png")
            raise
        if retain_all_frames:
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
    before_board: np.ndarray,
    minimum_wait: float,
    timeout: float,
    poll_seconds: float,
) -> Frame:
    time.sleep(minimum_wait)
    deadline = time.monotonic() + timeout
    previous: np.ndarray | None = None
    previous_frame: Frame | None = None
    last_error: ValueError | None = None
    transition_started = False
    board_changed = False
    while time.monotonic() < deadline:
        frame = source.capture()
        button = continue_button(frame.png)
        if button is not None:
            AdbActionSink(
                config.device_serial,
                config.swipe_duration_ms,
                config.capture_timeout_seconds,
            ).tap(button)
            time.sleep(1.0)
            transition_started = True
            previous = None
            continue
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
            # Settlement only observes stability. Move planning remains strict and
            # requires a subsequent frame with no unknown cells.
            board = _recognize_frame(frame.png, config, max_unknown=2)
        except ValueError as error:
            last_error = error
            time.sleep(poll_seconds)
            continue
        board_changed = board_changed or _board_changed_after_move(before_board, board)
        anchor_stable = (
            previous_frame is not None
            and foreground_change_fraction(previous_frame.png, frame.png, config)
            <= config.foreground_change_threshold
        )
        if (
            board_changed
            and anchor_stable
            and previous is not None
            and _boards_equivalent_for_settlement(previous, board)
        ):
            return frame
        previous = board
        previous_frame = frame
        time.sleep(poll_seconds)
    raise RuntimeError(f"board did not settle within {timeout:g}s: {last_error or 'changed'}")


def _board_changed_after_move(before: np.ndarray, current: np.ndarray) -> bool:
    if before.shape != current.shape:
        return True
    differing = before != current
    ordinary = (before < 7) & (current < 7)
    # A successful adjacent swap changes at least two ordinary cells. A single
    # difference can be an animated hint or recognition flicker.
    return int(np.count_nonzero(differing & ordinary)) >= 2


def _boards_equivalent_for_settlement(previous: np.ndarray, current: np.ndarray) -> bool:
    if previous.shape != current.shape:
        return False
    differing = previous != current
    difference_count = int(np.count_nonzero(differing))
    if difference_count == 0:
        return True
    special_or_unknown = (previous >= 7) | (current >= 7)
    ordinary_difference_count = int(np.count_nonzero(differing & ~special_or_unknown))
    # Several simultaneous flame and hint effects can perturb one cell each while
    # the underlying board remains stationary. The separate post-swipe change guard
    # still prevents a rejected swipe from being accepted as a completed turn.
    return ordinary_difference_count <= 8


def run_multi_turn(
    config: AppConfig,
    output_root: Path,
    turns: int,
    settle_seconds: float = 0.05,
    settle_timeout_seconds: float = 120.0,
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
