from pathlib import Path

import pytest

from bejeweled_player.config import load_config
from bejeweled_player.domain import Coordinate


PROFILE = Path(__file__).parents[1] / "config" / "target_720x1536.toml"
PIXEL_PROFILE = Path(__file__).parents[1] / "config" / "pixel9pro_960x2142.toml"


def test_initial_profile_loads() -> None:
    config = load_config(PROFILE)
    assert (config.geometry.rows, config.geometry.columns) == (8, 8)
    assert config.geometry.center(Coordinate(0, 0)) == (45, 363)


def test_pixel_9_pro_profile_loads() -> None:
    config = load_config(PIXEL_PROFILE)
    assert (config.screenshot_width, config.screenshot_height) == (960, 2142)
    assert config.geometry.center(Coordinate(0, 0)) == (60, 508)
    assert config.geometry.center(Coordinate(7, 7)) == (900, 1348)


def test_unknown_root_key_is_rejected(tmp_path: Path) -> None:
    text = "unsafe = true\n" + PROFILE.read_text()
    path = tmp_path / "invalid.toml"
    path.write_text(text)
    with pytest.raises(ValueError, match="unknown configuration keys"):
        load_config(path)
