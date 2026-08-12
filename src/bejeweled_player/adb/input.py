from __future__ import annotations

import uuid

from ..domain import Move
from ..interfaces import BoardGeometry
from .transport import AdbError, CommandRunner, _default_runner, _executable


class AdbActionSink:
    """Executes one validated board swipe; orchestration controls authorization."""

    def __init__(
        self,
        serial: str,
        duration_ms: int,
        timeout_seconds: float,
        *,
        runner: CommandRunner = _default_runner,
        executable: str | None = None,
    ) -> None:
        if not serial or any(character.isspace() for character in serial):
            raise ValueError("device serial must be non-empty and contain no whitespace")
        if duration_ms <= 0:
            raise ValueError("swipe duration must be positive")
        self._command = [executable or _executable(), "-s", serial]
        self._duration_ms = duration_ms
        self._timeout = timeout_seconds
        self._runner = runner

    def swipe(self, move: Move, geometry: BoardGeometry) -> str:
        start = geometry.center(move.source)
        end = geometry.center(move.destination)
        result = self._runner(
            [
                *self._command,
                "shell",
                "input",
                "swipe",
                str(start[0]),
                str(start[1]),
                str(end[0]),
                str(end[1]),
                str(self._duration_ms),
            ],
            self._timeout,
        )
        if result.returncode != 0:
            error = result.stderr.decode(errors="replace").strip()
            raise AdbError(f"swipe failed: {error or f'exit {result.returncode}'}")
        return uuid.uuid4().hex
