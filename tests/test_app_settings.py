"""Tests voor AppSettings persistentie via ConfigManager."""

from __future__ import annotations
import json
from pathlib import Path

import pytest

from app.settings import RenderSettings, ViewportSettings, AppSettings
from app.config_manager import ConfigManager


def test_app_settings_opslaan_en_laden(tmp_path: Path) -> None:
    """AppSettings.word_template_path blijft behouden na save/load."""
    mgr = ConfigManager(config_file=tmp_path / 'config.json')
    rs = RenderSettings()
    vp = ViewportSettings()
    app = AppSettings(word_template_path='C:/test/template.docx')

    mgr.save(rs, vp, app)
    _, _, geladen = mgr.load()

    assert geladen.word_template_path == 'C:/test/template.docx'


def test_laden_zonder_app_settings_geeft_default(tmp_path: Path) -> None:
    """Bestaand config-bestand zonder app_settings-sleutel geeft AppSettings() terug."""
    cfg_file = tmp_path / 'config.json'
    cfg_file.write_text('{"render_settings": {}, "viewport_settings": {}}', encoding='utf-8')
    mgr = ConfigManager(config_file=cfg_file)

    _, _, app = mgr.load()

    assert app.word_template_path == ''


def test_laden_zonder_bestand_geeft_defaults(tmp_path: Path) -> None:
    """Ontbrekend config-bestand geeft drie default-objecten terug."""
    mgr = ConfigManager(config_file=tmp_path / 'nieuw.json')

    rs, vp, app = mgr.load()

    assert isinstance(rs, RenderSettings)
    assert isinstance(vp, ViewportSettings)
    assert isinstance(app, AppSettings)
    assert app.word_template_path == ''
