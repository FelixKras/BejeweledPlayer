import subprocess

from bejeweled_player.adb import AdbActionSink
from bejeweled_player.domain import Coordinate, Move
from bejeweled_player.interfaces import BoardGeometry


def test_action_sink_builds_one_calibrated_swipe_command() -> None:
    commands = []

    def runner(command, timeout):
        commands.append((command, timeout))
        return subprocess.CompletedProcess(command, 0, b"", b"")

    sink = AdbActionSink(
        "phone:1234", 120, 5, runner=runner, executable="adb"
    )
    receipt = sink.swipe(
        Move(Coordinate(6, 4), Coordinate(6, 3)),
        BoardGeometry(8, 8, 0, 448, 960, 1408),
    )
    assert receipt
    assert commands == [
        (
            [
                "adb",
                "-s",
                "phone:1234",
                "shell",
                "input",
                "swipe",
                "540",
                "1228",
                "420",
                "1228",
                "120",
            ],
            5,
        )
    ]


def test_action_sink_builds_tap_command() -> None:
    commands = []

    def runner(command, timeout):
        commands.append((command, timeout))
        return subprocess.CompletedProcess(command, 0, b"", b"")

    sink = AdbActionSink("phone:1234", 120, 5, runner=runner, executable="adb")
    assert sink.tap((480, 1680))
    assert commands == [
        (["adb", "-s", "phone:1234", "shell", "input", "tap", "480", "1680"], 5)
    ]
