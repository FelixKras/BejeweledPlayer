from __future__ import annotations

import shutil
import subprocess
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import cv2
import numpy as np

from ..domain import Frame


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    details: tuple[str, ...] = ()


class AdbError(RuntimeError):
    pass


CommandRunner = Callable[[Sequence[str], float], subprocess.CompletedProcess[bytes]]


def _default_runner(command: Sequence[str], timeout: float) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise AdbError(f"ADB command timed out after {timeout:g}s") from error


def _executable() -> str:
    executable = shutil.which("adb")
    if executable is None:
        raise AdbError("adb was not found on PATH; install Android platform-tools")
    return executable


def list_devices(
    *, runner: CommandRunner = _default_runner, executable: str | None = None
) -> tuple[AdbDevice, ...]:
    result = runner([executable or _executable(), "devices", "-l"], 5.0)
    if result.returncode != 0:
        error = result.stderr.decode(errors="replace").strip()
        raise AdbError(f"ADB device discovery failed: {error or f'exit {result.returncode}'}")
    devices = []
    for line in result.stdout.decode(errors="replace").splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2:
            devices.append(AdbDevice(fields[0], fields[1], tuple(fields[2:])))
    return tuple(devices)


class AdbFrameSource:
    def __init__(
        self,
        serial: str,
        expected_size: tuple[int, int],
        timeout_seconds: float,
        retries: int,
        *,
        runner: CommandRunner = _default_runner,
        executable: str | None = None,
    ) -> None:
        if not serial or any(character.isspace() for character in serial):
            raise ValueError("device serial must be non-empty and contain no whitespace")
        self._command = [executable or _executable(), "-s", serial]
        self._expected_size = expected_size
        self._timeout = timeout_seconds
        self._retries = retries
        self._runner = runner

    def capture(self) -> Frame:
        last_error: AdbError | None = None
        for _ in range(self._retries + 1):
            try:
                return self._capture_once()
            except AdbError as error:
                last_error = error
        assert last_error is not None
        raise last_error

    def _capture_once(self) -> Frame:
        result = self._runner([*self._command, "exec-out", "screencap", "-p"], self._timeout)
        if result.returncode != 0:
            error = result.stderr.decode(errors="replace").strip()
            raise AdbError(f"screenshot failed: {error or f'exit {result.returncode}'}")
        image = cv2.imdecode(np.frombuffer(result.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise AdbError("screenshot command returned invalid PNG data")
        height, width = image.shape[:2]
        if (width, height) != self._expected_size:
            raise AdbError(
                f"expected {self._expected_size[0]}x{self._expected_size[1]} portrait frame, "
                f"received {width}x{height}"
            )
        return Frame(
            frame_id=uuid.uuid4().hex,
            monotonic_timestamp=time.monotonic(),
            png=result.stdout,
            width=width,
            height=height,
        )
