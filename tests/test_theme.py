"""Tests voor het thema-systeem (pure Python, geen Qt)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.theme import Theme, discover_themes


def _voorbeeld_thema_dict() -> dict:
    return {
        "name": "Test",
        "colors": {
            "primary": "#147ACF",
            "primary_hover": "#0d63ad",
            "primary_pressed": "#0a4f8a",
            "text": "#44546A",
            "text_muted": "#7a8794",
            "border": "#D8DFE6",
            "border_strong": "#aabdca",
            "surface": "#FFFFFF",
            "background": "#FAFBFC",
            "ok": "#309942",
            "warning": "#FF5C00",
            "danger": "#c0392b",
        },
        "typography": {
            "family": "Eina 04",
            "fallback": "Segoe UI",
            "size_base": 11,
            "size_title": 12,
            "size_small": 10,
        },
        "geometry": {
            "radius": 4,
            "spacing": 8,
            "padding_button": "7px 14px",
        },
        "assets": {
            "font_files": ["/pad/naar/font.ttf"],
            "app_logo": "/pad/naar/logo.png",
        },
    }


def test_load_valid_json(tmp_path: Path) -> None:
    pad = tmp_path / "test.json"
    pad.write_text(json.dumps(_voorbeeld_thema_dict()), encoding="utf-8")

    thema = Theme.load(pad)

    assert thema.name == "Test"
    assert thema.colors.primary == "#147ACF"
    assert thema.typography.family == "Eina 04"
    assert thema.geometry.radius == 4
    assert thema.assets.app_logo == "/pad/naar/logo.png"
    assert thema.assets.font_files == ["/pad/naar/font.ttf"]


def test_load_missing_required_field_raises(tmp_path: Path) -> None:
    data = _voorbeeld_thema_dict()
    del data["colors"]
    pad = tmp_path / "kapot.json"
    pad.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="colors"):
        Theme.load(pad)


def test_load_missing_optional_assets_ok(tmp_path: Path) -> None:
    data = _voorbeeld_thema_dict()
    del data["assets"]
    pad = tmp_path / "geen_assets.json"
    pad.write_text(json.dumps(data), encoding="utf-8")

    thema = Theme.load(pad)

    assert thema.assets.font_files == []
    assert thema.assets.app_logo == ""


def test_discover_themes_finds_json_files(tmp_path: Path) -> None:
    (tmp_path / "alpha.json").write_text(
        json.dumps(_voorbeeld_thema_dict()), encoding="utf-8"
    )
    (tmp_path / "bravo.json").write_text(
        json.dumps({**_voorbeeld_thema_dict(), "name": "Bravo"}),
        encoding="utf-8",
    )
    (tmp_path / "ignoreer.txt").write_text("nope", encoding="utf-8")

    profielen = discover_themes(tmp_path)

    assert len(profielen) == 2
    namen = sorted(p[0] for p in profielen)
    assert namen == ["Bravo", "Test"]


def test_discover_themes_skipt_kapotte_bestanden(tmp_path: Path) -> None:
    (tmp_path / "ok.json").write_text(
        json.dumps(_voorbeeld_thema_dict()), encoding="utf-8"
    )
    (tmp_path / "kapot.json").write_text("{niet geldig json", encoding="utf-8")

    profielen = discover_themes(tmp_path)

    assert len(profielen) == 1
    assert profielen[0][0] == "Test"


def test_build_stylesheet_bevat_kleuren_en_font(tmp_path: Path) -> None:
    pad = tmp_path / "test.json"
    pad.write_text(json.dumps(_voorbeeld_thema_dict()), encoding="utf-8")
    thema = Theme.load(pad)

    qss = thema.build_stylesheet(font_family="Eina 04")

    # Primaire kleur en knop-objectName
    assert "#147ACF" in qss
    assert "QPushButton#btnPrimary" in qss

    # Tekstkleur
    assert "#44546A" in qss

    # Font-familienaam met dubbele quotes (cruciaal voor namen met spatie)
    assert '"Eina 04"' in qss

    # GroupBox card-styling
    assert "QGroupBox" in qss

    # QTabBar selected-tab styling
    assert "QTabBar::tab:selected" in qss

    # QTabWidget pane top-overlap fix tegen dubbele lijn
    assert "QTabWidget::pane" in qss
    assert "top: -1px" in qss


def test_build_stylesheet_gebruikt_meegegeven_font(tmp_path: Path) -> None:
    """Als de werkelijke font-familienaam afwijkt van typography.family,
    dan gebruikt de stylesheet de meegegeven naam (niet die uit JSON)."""
    pad = tmp_path / "test.json"
    pad.write_text(json.dumps(_voorbeeld_thema_dict()), encoding="utf-8")
    thema = Theme.load(pad)

    qss = thema.build_stylesheet(font_family="Segoe UI")

    assert '"Segoe UI"' in qss
    assert '"Eina 04"' not in qss
