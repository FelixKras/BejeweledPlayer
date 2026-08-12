from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .domain import BoardObservation, Coordinate, Frame, Move


@dataclass(frozen=True)
class BoardGeometry:
    rows: int
    columns: int
    left: int
    top: int
    right: int
    bottom: int

    def center(self, coordinate: Coordinate) -> tuple[int, int]:
        if not (0 <= coordinate.row < self.rows and 0 <= coordinate.column < self.columns):
            raise ValueError("coordinate is outside the board")
        return (
            round(self.left + (coordinate.column + 0.5) * self.width / self.columns),
            round(self.top + (coordinate.row + 0.5) * self.height / self.rows),
        )

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


class FrameSource(Protocol):
    def capture(self) -> Frame: ...


class ActionSink(Protocol):
    def swipe(self, move: Move, geometry: BoardGeometry) -> str: ...


class BoardRecognizer(Protocol):
    def recognize(self, frames: Sequence[Frame]) -> BoardObservation: ...


class FakeFrameSource:
    def __init__(self, frames: Sequence[Frame]) -> None:
        self._frames = iter(frames)

    def capture(self) -> Frame:
        return next(self._frames)


class FakeActionSink:
    def __init__(self) -> None:
        self.actions: list[tuple[Move, BoardGeometry]] = []

    def swipe(self, move: Move, geometry: BoardGeometry) -> str:
        self.actions.append((move, geometry))
        return f"fake-action-{len(self.actions)}"
