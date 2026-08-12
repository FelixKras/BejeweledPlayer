import pytest

from bejeweled_player.domain import Coordinate, Move
from bejeweled_player.interfaces import BoardGeometry, FakeActionSink


def test_geometry_maps_first_and_last_cells() -> None:
    geometry = BoardGeometry(8, 8, 0, 320, 720, 1005)
    assert geometry.center(Coordinate(0, 0)) == (45, 363)
    assert geometry.center(Coordinate(7, 7)) == (675, 962)


def test_move_must_be_adjacent() -> None:
    with pytest.raises(ValueError, match="adjacent"):
        Move(Coordinate(0, 0), Coordinate(0, 2))


def test_fake_sink_records_without_hardware() -> None:
    geometry = BoardGeometry(8, 8, 0, 320, 720, 1005)
    move = Move(Coordinate(0, 0), Coordinate(0, 1))
    sink = FakeActionSink()
    assert sink.swipe(move, geometry) == "fake-action-1"
    assert sink.actions == [(move, geometry)]
