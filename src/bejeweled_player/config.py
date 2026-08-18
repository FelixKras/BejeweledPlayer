from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .interfaces import BoardGeometry

_ROOT_KEYS = {
    "schema_version",
    "device",
    "capture",
    "geometry",
    "recognition",
    "rules",
    "planner",
    "action",
    "logging",
    "ui_detection",
}


@dataclass(frozen=True)
class AppConfig:
    schema_version: int
    device_serial: str
    screenshot_width: int
    screenshot_height: int
    capture_timeout_seconds: float
    capture_retries: int
    geometry: BoardGeometry
    recognizer_profile: str
    rule_set: str
    random_seed: int
    planning_budget_seconds: float
    swipe_duration_ms: int
    frame_retention: str
    progress_region: tuple[int, int, int, int]
    progress_full_threshold: float
    foreground_region: tuple[int, int, int, int] = (0, 0, 1, 1)
    foreground_change_threshold: float = 0.08


def _section(data: Mapping[str, Any], name: str, allowed: set[str]) -> Mapping[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise TypeError(f"[{name}] section is required")
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"unknown [{name}] keys: {', '.join(sorted(unknown))}")
    return value


def load_config(path: Path) -> AppConfig:
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    unknown = set(data) - _ROOT_KEYS
    if unknown:
        raise ValueError(f"unknown configuration keys: {', '.join(sorted(unknown))}")
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")

    device = _section(data, "device", {"serial"})
    capture = _section(data, "capture", {"width", "height", "timeout_seconds", "retries"})
    geometry = _section(
        data, "geometry", {"rows", "columns", "left", "top", "right", "bottom"}
    )
    recognition = _section(data, "recognition", {"profile"})
    rules = _section(data, "rules", {"rule_set"})
    planner = _section(data, "planner", {"random_seed", "budget_seconds"})
    action = _section(data, "action", {"swipe_duration_ms"})
    logging = _section(data, "logging", {"frame_retention"})
    ui = _section(
        data,
        "ui_detection",
        {
            "progress_left",
            "progress_top",
            "progress_right",
            "progress_bottom",
            "progress_full_threshold",
            "foreground_left",
            "foreground_top",
            "foreground_right",
            "foreground_bottom",
            "foreground_change_threshold",
        },
    )

    result = AppConfig(
        schema_version=1,
        device_serial=str(device["serial"]),
        screenshot_width=int(capture["width"]),
        screenshot_height=int(capture["height"]),
        capture_timeout_seconds=float(capture["timeout_seconds"]),
        capture_retries=int(capture["retries"]),
        geometry=BoardGeometry(**{key: int(value) for key, value in geometry.items()}),
        recognizer_profile=str(recognition["profile"]),
        rule_set=str(rules["rule_set"]),
        random_seed=int(planner["random_seed"]),
        planning_budget_seconds=float(planner["budget_seconds"]),
        swipe_duration_ms=int(action["swipe_duration_ms"]),
        frame_retention=str(logging["frame_retention"]),
        progress_region=(
            int(ui["progress_left"]),
            int(ui["progress_top"]),
            int(ui["progress_right"]),
            int(ui["progress_bottom"]),
        ),
        progress_full_threshold=float(ui["progress_full_threshold"]),
        foreground_region=(
            int(ui["foreground_left"]),
            int(ui["foreground_top"]),
            int(ui["foreground_right"]),
            int(ui["foreground_bottom"]),
        ),
        foreground_change_threshold=float(ui["foreground_change_threshold"]),
    )
    _validate(result)
    return result


def _validate(config: AppConfig) -> None:
    geometry = config.geometry
    if config.screenshot_width <= 0 or config.screenshot_height <= config.screenshot_width:
        raise ValueError("capture dimensions must describe a portrait screenshot")
    if (geometry.rows, geometry.columns) != (8, 8):
        raise ValueError("initial profile requires an 8x8 board")
    if not (0 <= geometry.left < geometry.right <= config.screenshot_width):
        raise ValueError("horizontal board bounds are outside the screenshot")
    if not (0 <= geometry.top < geometry.bottom <= config.screenshot_height):
        raise ValueError("vertical board bounds are outside the screenshot")
    if config.planning_budget_seconds <= 0 or config.swipe_duration_ms <= 0:
        raise ValueError("planner budget and swipe duration must be positive")
    if config.capture_timeout_seconds <= 0 or config.capture_retries < 0:
        raise ValueError("capture timeout must be positive and retries cannot be negative")
    if config.frame_retention not in {"all", "decision", "errors", "none"}:
        raise ValueError("frame_retention must be all, decision, errors, or none")
    left, top, right, bottom = config.progress_region
    if not (0 <= left < right <= config.screenshot_width and 0 <= top < bottom <= config.screenshot_height):
        raise ValueError("progress region is outside the screenshot")
    if not 0 < config.progress_full_threshold <= 1:
        raise ValueError("progress_full_threshold must be between 0 and 1")
    left, top, right, bottom = config.foreground_region
    if not (0 <= left < right <= config.screenshot_width and 0 <= top < bottom <= config.screenshot_height):
        raise ValueError("foreground region is outside the screenshot")
    if not 0 <= config.foreground_change_threshold <= 1:
        raise ValueError("foreground change threshold must be between 0 and 1")
