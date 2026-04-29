"""Tests voor het thema-systeem (pure Python, geen Qt)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.theme import Theme


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
