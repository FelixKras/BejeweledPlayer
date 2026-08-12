import subprocess

import cv2
import numpy as np
import pytest

from bejeweled_player.adb import AdbDevice, AdbError, AdbFrameSource, list_devices


def completed(stdout: bytes = b"", stderr: bytes = b"", code: int = 0):
    return subprocess.CompletedProcess(["adb"], code, stdout, stderr)


def test_device_listing_parses_state_and_details() -> None:
    def runner(command, timeout):
        return completed(
            b"List of devices attached\n192.168.1.8:5555 device product:test model:Phone\n"
        )

    assert list_devices(runner=runner, executable="adb") == (
        AdbDevice("192.168.1.8:5555", "device", ("product:test", "model:Phone")),
    )


def test_capture_returns_validated_lossless_frame() -> None:
    image = np.zeros((1536, 720, 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)
    assert success
    source = AdbFrameSource(
        "device:5555",
        (720, 1536),
        1,
        0,
        runner=lambda command, timeout: completed(encoded.tobytes()),
        executable="adb",
    )
    frame = source.capture()
    assert (frame.width, frame.height) == (720, 1536)
    assert frame.png == encoded.tobytes()


def test_capture_rejects_wrong_resolution() -> None:
    success, encoded = cv2.imencode(".png", np.zeros((100, 100, 3), dtype=np.uint8))
    assert success
    source = AdbFrameSource(
        "device:5555",
        (720, 1536),
        1,
        0,
        runner=lambda command, timeout: completed(encoded.tobytes()),
        executable="adb",
    )
    with pytest.raises(AdbError, match="expected 720x1536"):
        source.capture()
