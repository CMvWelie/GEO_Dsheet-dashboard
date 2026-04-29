"""Test dat active_theme_name in AppSettings wordt opgeslagen en geladen."""

from __future__ import annotations

from pathlib import Path

from app.config_manager import ConfigManager
from app.settings import AppSettings, RenderSettings, ViewportSettings


def test_active_theme_name_default_is_dkib() -> None:
    app = AppSettings()
    assert app.active_theme_name == "DKIB"


def test_config_manager_round_trip_active_theme(tmp_path: Path) -> None:
    cfg_pad = tmp_path / "config.json"
    cm = ConfigManager(config_file=cfg_pad)

    app = AppSettings(active_theme_name="SixGeoConsult")
    cm.save(RenderSettings(), ViewportSettings(), app)

    _, _, app_geladen = cm.load()
    assert app_geladen.active_theme_name == "SixGeoConsult"


def test_config_manager_oude_config_zonder_theme_geeft_default(tmp_path: Path) -> None:
    """Oudere config-bestanden zonder active_theme_name moeten default krijgen."""
    cfg_pad = tmp_path / "config.json"
    cfg_pad.write_text(
        '{"render_settings": {}, "viewport_settings": {}, '
        '"app_settings": {"word_template_path": "/x.dotx"}}',
        encoding="utf-8",
    )
    cm = ConfigManager(config_file=cfg_pad)

    _, _, app = cm.load()
    assert app.active_theme_name == "DKIB"
    assert app.word_template_path == "/x.dotx"
