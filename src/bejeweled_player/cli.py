from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .adb import AdbActionSink, AdbError, AdbFrameSource, list_devices
from .config import AppConfig, load_config
from .domain import Coordinate, Move
from .turn import run_multi_turn, run_turn, run_unbounded
from .vision import render_grid_overlay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autoplayer")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("devices", help="list ADB devices without sending input")

    validate = commands.add_parser("validate-config", help="validate a TOML profile")
    validate.add_argument("--config", type=Path, required=True)

    observe = commands.add_parser("observe", help="capture one frame and render board geometry")
    observe.add_argument("--config", type=Path, required=True)
    observe.add_argument("--output-dir", type=Path, default=Path("sessions"))

    render = commands.add_parser("render-debug", help="overlay configured geometry on a PNG")
    render.add_argument("--config", type=Path, required=True)
    render.add_argument("--frame", type=Path, required=True)
    render.add_argument("--output", type=Path, required=True)

    swipe = commands.add_parser("swipe", help="perform at most one adjacent board swipe")
    swipe.add_argument("--config", type=Path, required=True)
    swipe.add_argument("--source", nargs=2, type=int, metavar=("ROW", "COLUMN"), required=True)
    swipe.add_argument("--destination", nargs=2, type=int, metavar=("ROW", "COLUMN"), required=True)
    swipe.add_argument(
        "--execute", action="store_true", help="authorize this one swipe; otherwise dry-run"
    )

    turn = commands.add_parser("turn", help="capture, choose one immediate match, and exit")
    turn.add_argument("--config", type=Path, required=True)
    turn.add_argument("--output-dir", type=Path, default=Path("sessions"))
    turn.add_argument("--settle-seconds", type=float, default=0.05)
    turn.add_argument("--execute", action="store_true", help="authorize the selected single swipe")

    multi_turn = commands.add_parser(
        "multi-turn", help="run a bounded sequence of recorded immediate-match turns"
    )
    multi_turn.add_argument("--config", type=Path, required=True)
    multi_turn.add_argument("--turns", type=int, required=True)
    multi_turn.add_argument("--output-dir", type=Path, default=Path("sessions"))
    multi_turn.add_argument("--settle-seconds", type=float, default=0.05)
    multi_turn.add_argument("--execute", action="store_true", help="authorize the bounded sequence")

    play = commands.add_parser(
        "play", help="play until stopped; one immediate-score turn at a time"
    )
    play.add_argument("--config", type=Path, required=True)
    play.add_argument("--output-dir", type=Path, default=Path("sessions"))
    play.add_argument("--settle-minimum-seconds", type=float, default=0.05)
    play.add_argument("--settle-timeout-seconds", type=float, default=25.0)
    play.add_argument("--poll-seconds", type=float, default=0.08)
    play.add_argument("--execute", action="store_true", help="required safety authorization")

    for name in ("calibrate", "suggest", "replay", "simulate"):
        commands.add_parser(name).set_defaults(unimplemented=True)
    return parser


def _frame_source(config: AppConfig) -> AdbFrameSource:
    if config.device_serial.startswith("CHANGE_ME"):
        raise ValueError("set [device].serial to the authorised device serial or IP:port")
    return AdbFrameSource(
        config.device_serial,
        (config.screenshot_width, config.screenshot_height),
        config.capture_timeout_seconds,
        config.capture_retries,
    )


def _devices() -> None:
    devices = list_devices()
    if not devices:
        print("No ADB devices found. Input is DISABLED.")
        return
    print("SERIAL\tSTATE\tDETAILS")
    for device in devices:
        print(f"{device.serial}\t{device.state}\t{' '.join(device.details)}")
    print("Input is DISABLED.")


def _observe(config: AppConfig, output_root: Path) -> None:
    frame = _frame_source(config).capture()
    session = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    session.mkdir(parents=True, exist_ok=False)
    raw_path = session / f"{frame.frame_id}.png"
    overlay_path = session / f"{frame.frame_id}.overlay.png"
    raw_path.write_bytes(frame.png)
    render_grid_overlay(frame.png, config.geometry, overlay_path)
    print(
        f"OBSERVE-ONLY input=DISABLED frame={frame.frame_id} "
        f"size={frame.width}x{frame.height} overlay={overlay_path}"
    )


def _swipe(config: AppConfig, source: list[int], destination: list[int], execute: bool) -> None:
    move = Move(Coordinate(*source), Coordinate(*destination))
    start = config.geometry.center(move.source)
    end = config.geometry.center(move.destination)
    if not execute:
        print(
            f"DRY-RUN input=DISABLED move={move.source}->{move.destination} "
            f"pixels={start}->{end}; pass --execute to authorize exactly one swipe"
        )
        return
    receipt = AdbActionSink(
        config.device_serial,
        config.swipe_duration_ms,
        config.capture_timeout_seconds,
    ).swipe(move, config.geometry)
    print(
        f"SWIPE-SENT action={receipt} move={move.source}->{move.destination} "
        f"pixels={start}->{end} outstanding=0"
    )


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "devices":
            _devices()
            return
        if args.command == "validate-config":
            config = load_config(args.config)
            print(
                f"valid schema={config.schema_version} geometry="
                f"{config.geometry.rows}x{config.geometry.columns} input=DISABLED"
            )
            return
        if args.command == "observe":
            _observe(load_config(args.config), args.output_dir)
            return
        if args.command == "render-debug":
            config = load_config(args.config)
            render_grid_overlay(args.frame.read_bytes(), config.geometry, args.output)
            print(f"rendered={args.output} input=DISABLED")
            return
        if args.command == "swipe":
            _swipe(load_config(args.config), args.source, args.destination, args.execute)
            return
        if args.command == "turn":
            if args.settle_seconds < 0:
                raise ValueError("settle-seconds cannot be negative")
            config = load_config(args.config)
            selected, action_id, session = run_turn(
                config, args.output_dir, args.execute, args.settle_seconds
            )
            if selected is None:
                print(f"NO-MOVE input=DISABLED session={session}")
                return
            mode = "SWIPE-SENT" if action_id else "DRY-RUN"
            print(
                f"{mode} move={selected.start}->{selected.end} score={selected.score} "
                f"action={action_id or 'none'} session={session}"
            )
            return
        if args.command == "multi-turn":
            if not 1 <= args.turns <= 100:
                raise ValueError("turns must be between 1 and 100")
            if args.settle_seconds < 0:
                raise ValueError("settle-seconds cannot be negative")
            if not args.execute:
                raise ValueError("multi-turn requires --execute authorization")
            session, records = run_multi_turn(
                load_config(args.config),
                args.output_dir,
                args.turns,
                args.settle_seconds,
            )
            print(f"MULTI-TURN completed={len(records)} session={session}")
            return
        if args.command == "play":
            if not args.execute:
                raise ValueError("play requires --execute authorization")
            if (
                args.settle_minimum_seconds < 0
                or args.settle_timeout_seconds <= 0
                or args.poll_seconds <= 0
            ):
                raise ValueError(
                    "settle minimum must be non-negative; timeout and poll must be positive"
                )
            session, records = run_unbounded(
                load_config(args.config),
                args.output_dir,
                args.settle_minimum_seconds,
                args.settle_timeout_seconds,
                args.poll_seconds,
            )
            print(f"PLAY stopped completed={len(records)} session={session}")
            return
    except (AdbError, OSError, ValueError) as error:
        raise SystemExit(f"error: {error}; input remains DISABLED") from error
    raise SystemExit(f"'{args.command}' is gated and not implemented; input remains disabled")


if __name__ == "__main__":
    main()
