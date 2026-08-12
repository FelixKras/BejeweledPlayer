from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class GemType(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    PURPLE = "purple"
    ORANGE = "orange"
    WHITE = "white"
    SPECIAL_1 = "special_1"
    SPECIAL_2 = "special_2"
    SPECIAL_3 = "special_3"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class EffectType(StrEnum):
    NONE = "none"
    SPARKLE = "sparkle"
    GLOW = "glow"
    SELECTED = "selected"
    HINT = "hint"
    MOVING = "moving"
    EXPLODING = "exploding"
    SPECIAL_UNKNOWN = "special_unknown"
    UNKNOWN = "unknown"


@dataclass(frozen=True, order=True)
class Coordinate:
    row: int
    column: int


@dataclass(frozen=True)
class Move:
    source: Coordinate
    destination: Coordinate

    def __post_init__(self) -> None:
        distance = abs(self.source.row - self.destination.row) + abs(
            self.source.column - self.destination.column
        )
        if distance != 1:
            raise ValueError("move endpoints must be orthogonally adjacent")


@dataclass(frozen=True)
class Frame:
    frame_id: str
    monotonic_timestamp: float
    png: bytes
    width: int
    height: int


@dataclass(frozen=True)
class CellObservation:
    coordinate: Coordinate
    gem_type: GemType
    effect: EffectType
    identity_confidence: float
    effect_confidence: float
    feature_summary: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    frame_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BoardObservation:
    cells: tuple[tuple[CellObservation, ...], ...]
    board_confidence: float
    stable: bool
    timestamp: float
    geometry_profile: str
    recognizer_profile: str


@dataclass(frozen=True)
class BoardState:
    """Symbolic simulator input, deliberately distinct from visual observations."""

    cells: tuple[tuple[GemType, ...], ...]
