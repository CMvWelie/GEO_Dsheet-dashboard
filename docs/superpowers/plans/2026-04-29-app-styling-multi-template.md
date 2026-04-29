# App-styling en multi-template — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centraliseer alle UI-styling in een thema-systeem aangedreven door JSON-themabestanden, en pas het toe op Tab Rapportcontext + Tab Instellingen volgens DKIB-huisstijl. Maak het uitbreidbaar met andere bedrijfsprofielen.

**Architecture:** Pure Python `app/theme.py` (dataclass + JSON-loader + stylesheet-generator), Qt-aware `app/theme_apply.py` (font-registratie + `setStyleSheet`). Bootstrap in `run.pyw` vóór `MainWindow()`. Thema-keuze persistent via `AppSettings.active_theme_name`; wissel vereist app-herstart.

**Tech Stack:** Python 3.10+, PyQt6, pytest, JSON

---

## Bestandsoverzicht

| Bestand | Wijziging |
|---|---|
| `themes/dkib.json` | Nieuw — DKIB-thema |
| `themes/sixgeoconsult.json` | Nieuw — SixGeoConsult-thema |
| `app/theme.py` | Nieuw — `Theme` dataclass, `load()`, `build_stylesheet()`, `discover_themes()` |
| `app/theme_apply.py` | Nieuw — `bootstrap_theme()` (Qt-aware) |
| `tests/test_theme.py` | Nieuw — pytest-tests voor pure Python deel |
| `app/settings.py` | `AppSettings.active_theme_name` toevoegen |
| `run.pyw` | `bootstrap_theme()` aanroepen vóór `MainWindow()` |
| `app/main_window.py` | Theme-parameter ontvangen, TopLeft cornerwidget met logo, `objectName` op export-knop, `_BTN_PRIMARY` op export-knop verwijderen |
| `ui/tabs/tab_report_context.py` | Lokale `_BTN_PRIMARY`/`_BTN_DANGER` weg; `objectName`s op knoppen |
| `ui/tabs/tab_instellingen.py` | Lokale `_BTN_NORMAL`/`_BTN_CLEAR` weg; `objectName`s op knoppen; nieuwe Template-groep |

---

## Task 1: Maak `themes/dkib.json` en `themes/sixgeoconsult.json`

**Files:**
- Create: `themes/dkib.json`
- Create: `themes/sixgeoconsult.json`

- [ ] **Stap 1: Maak themes-directory en `dkib.json`**

Maak `themes/dkib.json` met deze inhoud (let op: forward slashes in pad — werkt op Windows):

```json
{
  "name": "DKIB",
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
    "danger": "#c0392b"
  },
  "typography": {
    "family": "Eina 04",
    "fallback": "Segoe UI",
    "size_base": 11,
    "size_title": 12,
    "size_small": 10
  },
  "geometry": {
    "radius": 4,
    "spacing": 8,
    "padding_button": "7px 14px"
  },
  "assets": {
    "font_files": [
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-Regular.ttf",
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-SemiBold.ttf",
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-Bold.ttf"
    ],
    "app_logo": "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/DKIB_logo.png"
  }
}
```

- [ ] **Stap 2: Maak `themes/sixgeoconsult.json`**

Voorlopig met placeholder-kleuren (afgeleid van het SixGeoConsult-logo); content kan in een vervolgronde verfijnd worden door het Excel-template te inspecteren met dezelfde methode als bij DKIB.

```json
{
  "name": "SixGeoConsult",
  "colors": {
    "primary": "#7a4f9f",
    "primary_hover": "#5e3d7c",
    "primary_pressed": "#472d5d",
    "text": "#2c3e50",
    "text_muted": "#7a8794",
    "border": "#D8DFE6",
    "border_strong": "#aabdca",
    "surface": "#FFFFFF",
    "background": "#FAFBFC",
    "ok": "#309942",
    "warning": "#FF5C00",
    "danger": "#c0392b"
  },
  "typography": {
    "family": "Calibri",
    "fallback": "Segoe UI",
    "size_base": 11,
    "size_title": 12,
    "size_small": 10
  },
  "geometry": {
    "radius": 4,
    "spacing": 8,
    "padding_button": "7px 14px"
  },
  "assets": {
    "font_files": [],
    "app_logo": "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/SIXGeoConsult_logo.jpg"
  }
}
```

- [ ] **Stap 3: Commit**

```bash
git add themes/dkib.json themes/sixgeoconsult.json
git commit -m "feat: voeg DKIB en SixGeoConsult themabestanden toe"
```

---

## Task 2: `Theme` dataclass + `load()` met tests

**Files:**
- Create: `app/theme.py`
- Create: `tests/test_theme.py`

- [ ] **Stap 1: Schrijf falende tests voor `Theme.load()`**

Maak `tests/test_theme.py` met:

```python
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
```

- [ ] **Stap 2: Run tests om falen te bevestigen**

```bash
pytest tests/test_theme.py -v
```

Verwacht: `ImportError: cannot import name 'Theme' from 'app.theme'` (bestand bestaat nog niet).

- [ ] **Stap 3: Implementeer `app/theme.py`**

Maak `app/theme.py`:

```python
"""Thema-systeem voor de UI (pure Python, geen Qt-imports).

Een Theme bestaat uit een naam, kleuren, typografie, geometrie en assets.
Wordt geladen vanuit JSON-bestand en kan een Qt-stylesheet-string genereren.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ThemeColors:
    """Kleurpalet voor het thema."""
    primary: str
    primary_hover: str
    primary_pressed: str
    text: str
    text_muted: str
    border: str
    border_strong: str
    surface: str
    background: str
    ok: str
    warning: str
    danger: str


@dataclass
class ThemeTypography:
    """Typografie-instellingen."""
    family: str
    fallback: str
    size_base: int
    size_title: int
    size_small: int


@dataclass
class ThemeGeometry:
    """Geometrie-instellingen (radii, spacings)."""
    radius: int
    spacing: int
    padding_button: str


@dataclass
class ThemeAssets:
    """Asset-paden (fonts, logos)."""
    font_files: list[str] = field(default_factory=list)
    app_logo: str = ''


@dataclass
class Theme:
    """Volledige thema-definitie."""
    name: str
    colors: ThemeColors
    typography: ThemeTypography
    geometry: ThemeGeometry
    assets: ThemeAssets

    @classmethod
    def load(cls, path: Path) -> 'Theme':
        """Laad een thema vanuit een JSON-bestand.

        Parameters
        ----------
        path:
            Pad naar het JSON-themabestand.

        Returns
        -------
        Theme
            Het geladen thema.

        Raises
        ------
        ValueError
            Als een verplichte sectie (`colors`, `typography`, `geometry`)
            ontbreekt of als een verplicht veld binnen een sectie ontbreekt.
        """
        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        for vereist in ('colors', 'typography', 'geometry'):
            if vereist not in data:
                raise ValueError(f"Themabestand mist verplichte sectie '{vereist}'")

        try:
            colors = ThemeColors(**data['colors'])
            typography = ThemeTypography(**data['typography'])
            geometry = ThemeGeometry(**data['geometry'])
        except TypeError as exc:
            raise ValueError(f'Ongeldige thema-inhoud: {exc}') from exc

        assets_data = data.get('assets') or {}
        assets = ThemeAssets(
            font_files=list(assets_data.get('font_files', [])),
            app_logo=assets_data.get('app_logo', ''),
        )

        return cls(
            name=str(data.get('name', path.stem)),
            colors=colors,
            typography=typography,
            geometry=geometry,
            assets=assets,
        )
```

- [ ] **Stap 4: Run tests om slagen te bevestigen**

```bash
pytest tests/test_theme.py -v
```

Verwacht: 3 tests passed.

- [ ] **Stap 5: Commit**

```bash
git add app/theme.py tests/test_theme.py
git commit -m "feat: voeg Theme-dataclass en JSON-loader toe"
```

---

## Task 3: `discover_themes()` voor multi-template ontdekking

**Files:**
- Modify: `app/theme.py`
- Modify: `tests/test_theme.py`

- [ ] **Stap 1: Voeg falende test toe**

Voeg toe aan `tests/test_theme.py`:

```python
from app.theme import Theme, discover_themes


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
```

- [ ] **Stap 2: Run tests om falen te bevestigen**

```bash
pytest tests/test_theme.py::test_discover_themes_finds_json_files -v
```

Verwacht: `ImportError: cannot import name 'discover_themes'`.

- [ ] **Stap 3: Implementeer `discover_themes()`**

Voeg toe onderaan `app/theme.py`:

```python
def discover_themes(themes_dir: Path) -> list[tuple[str, Path]]:
    """Vind alle geldige thema-JSON-bestanden in een directory.

    Parameters
    ----------
    themes_dir:
        Map om te scannen op `*.json`-themabestanden.

    Returns
    -------
    list[tuple[str, Path]]
        Lijst van (naam, pad)-paren, gesorteerd op naam.
        Bestanden die niet als geldig thema kunnen worden geladen worden overgeslagen.
    """
    if not themes_dir.exists():
        return []

    gevonden: list[tuple[str, Path]] = []
    for pad in sorted(themes_dir.glob('*.json')):
        try:
            thema = Theme.load(pad)
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        gevonden.append((thema.name, pad))

    gevonden.sort(key=lambda paar: paar[0])
    return gevonden
```

- [ ] **Stap 4: Run tests**

```bash
pytest tests/test_theme.py -v
```

Verwacht: 5 tests passed.

- [ ] **Stap 5: Commit**

```bash
git add app/theme.py tests/test_theme.py
git commit -m "feat: voeg discover_themes() toe voor multi-template ontdekking"
```

---

## Task 4: `Theme.build_stylesheet()` — genereer Qt-QSS

**Files:**
- Modify: `app/theme.py`
- Modify: `tests/test_theme.py`

- [ ] **Stap 1: Voeg falende test toe**

Voeg toe aan `tests/test_theme.py`:

```python
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
```

- [ ] **Stap 2: Run om falen te bevestigen**

```bash
pytest tests/test_theme.py::test_build_stylesheet_bevat_kleuren_en_font -v
```

Verwacht: `AttributeError: 'Theme' object has no attribute 'build_stylesheet'`.

- [ ] **Stap 3: Implementeer `build_stylesheet()`**

Voeg toe aan de `Theme`-klasse in `app/theme.py` (vóór de `@classmethod load`):

```python
    def build_stylesheet(self, font_family: str) -> str:
        """Genereer een Qt-QSS-string voor deze thema.

        Parameters
        ----------
        font_family:
            De werkelijke font-familienaam zoals Qt deze rapporteert na
            `QFontDatabase.addApplicationFont()`. Kan afwijken van
            `typography.family` in het JSON-bestand.

        Returns
        -------
        str
            Een complete QSS-string voor `QApplication.setStyleSheet()`.
        """
        c = self.colors
        t = self.typography
        g = self.geometry
        ff = f'"{font_family}"'

        return f"""
* {{
    font-family: {ff}, "{t.fallback}", sans-serif;
    font-size: {t.size_base}pt;
    color: {c.text};
}}

QWidget {{
    background: {c.background};
}}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPlainTextEdit, QTextEdit {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    padding: 3px 6px;
    color: {c.text};
}}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {c.primary};
}}

QGroupBox {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius + 2}px;
    margin-top: 10px;
    padding: 10px 8px 6px 8px;
    font-weight: 600;
    color: {c.primary};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: {c.primary};
    font-size: {t.size_title}pt;
}}

QPushButton {{
    background: {c.surface};
    color: {c.text};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    padding: {g.padding_button};
    font-size: {t.size_base}pt;
    font-weight: 500;
}}

QPushButton:hover {{
    background: {c.background};
    border: 1px solid {c.border_strong};
}}

QPushButton:pressed {{
    background: {c.border};
}}

QPushButton:disabled {{
    color: {c.text_muted};
    background: {c.background};
    border: 1px solid {c.border};
}}

QPushButton#btnPrimary {{
    background: {c.primary};
    color: {c.surface};
    border: 1px solid {c.primary_hover};
    font-weight: 600;
}}

QPushButton#btnPrimary:hover {{
    background: {c.primary_hover};
}}

QPushButton#btnPrimary:pressed {{
    background: {c.primary_pressed};
}}

QPushButton#btnDanger {{
    background: {c.surface};
    color: {c.danger};
    border: 1px solid {c.danger};
}}

QPushButton#btnDanger:hover {{
    background: #fdf0ee;
}}

QPushButton#btnNormal {{
    background: {c.surface};
    color: {c.text};
    border: 1px solid {c.border};
}}

QPushButton#btnClear {{
    background: {c.surface};
    color: {c.text_muted};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    font-size: {t.size_small}pt;
    padding: 2px 4px;
}}

QPushButton#btnClear:hover {{
    color: {c.danger};
    border-color: {c.danger};
}}

QTabWidget::pane {{
    border-top: 1px solid {c.border};
    background: {c.surface};
    top: -1px;
}}

QTabBar::tab {{
    background: {c.background};
    color: {c.text};
    padding: 6px 14px;
    border: 1px solid {c.border};
    border-bottom: none;
    border-top-left-radius: {g.radius}px;
    border-top-right-radius: {g.radius}px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {c.surface};
    color: {c.primary};
    border-top: 3px solid {c.primary};
    font-weight: 600;
}}

QTabBar::tab:!selected:hover {{
    background: {c.surface};
}}

QListWidget {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
}}

QListWidget::item:selected {{
    background: {c.primary};
    color: {c.surface};
}}

QLabel {{
    background: transparent;
    color: {c.text};
}}

QLabel#hintLabel {{
    color: {c.text_muted};
    font-size: {t.size_small}pt;
    font-style: italic;
}}

QLabel#projectLabel {{
    font-size: {t.size_small}pt;
    font-weight: 600;
    color: {c.text};
}}
""".strip()
```

- [ ] **Stap 4: Run tests**

```bash
pytest tests/test_theme.py -v
```

Verwacht: 7 tests passed.

- [ ] **Stap 5: Commit**

```bash
git add app/theme.py tests/test_theme.py
git commit -m "feat: voeg Theme.build_stylesheet() toe voor Qt-QSS-generatie"
```

---

## Task 5: `AppSettings.active_theme_name` veld + persistentie

**Files:**
- Modify: `app/settings.py:54-60`
- Create: `tests/test_app_settings_theme.py`

- [ ] **Stap 1: Schrijf falende test voor persistentie**

Maak `tests/test_app_settings_theme.py`:

```python
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
```

- [ ] **Stap 2: Run om falen te bevestigen**

```bash
pytest tests/test_app_settings_theme.py -v
```

Verwacht: `AttributeError: 'AppSettings' object has no attribute 'active_theme_name'`.

- [ ] **Stap 3: Voeg veld toe in `app/settings.py`**

In `app/settings.py`, vervang de hele `AppSettings`-klasse:

```python
@dataclass
class AppSettings:
    """Algemene applicatie-instellingen."""
    word_template_path: str = ''
    """Pad naar het Word-sjabloon (.dotx, ook .docx ondersteund); leeg = geen sjabloon."""
    standaard_importmap: str = ''
    """Standaard startmap voor het importeer-dialoogvenster; leeg = systeemstandaard."""
    active_theme_name: str = 'DKIB'
    """Naam van het actieve UI-thema; verwijst naar `themes/<naam>.json`."""
```

- [ ] **Stap 4: Run tests**

```bash
pytest tests/test_app_settings_theme.py -v
```

Verwacht: 3 tests passed. Het bestaande `ConfigManager.load()` filtert al op `__dataclass_fields__` dus oude configs zonder het veld werken automatisch.

- [ ] **Stap 5: Run alle bestaande tests om regressies te vangen**

```bash
pytest tests/ -v
```

Verwacht: alle tests slagen, geen nieuwe fouten.

- [ ] **Stap 6: Commit**

```bash
git add app/settings.py tests/test_app_settings_theme.py
git commit -m "feat: voeg active_theme_name toe aan AppSettings"
```

---

## Task 6: `app/theme_apply.py` — Qt-bootstrap

**Files:**
- Create: `app/theme_apply.py`

Dit is het Qt-aware deel. Geen unit-tests (vereist `QApplication`); wordt visueel gevalideerd in Task 13.

- [ ] **Stap 1: Implementeer `app/theme_apply.py`**

Maak `app/theme_apply.py`:

```python
"""Qt-aware bootstrap voor het thema-systeem.

Verantwoordelijk voor het registreren van fonts en het toepassen van de
gegenereerde stylesheet op de QApplication. Gescheiden van `theme.py`
zodat de pure Python-logica los van Qt getest kan worden.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from app.theme import Theme

THEMES_DIR = Path(__file__).resolve().parent.parent / 'themes'
DEFAULT_THEME = 'DKIB'


def bootstrap_theme(actief_thema_naam: str) -> Theme | None:
    """Laad het thema, registreer fonts en pas stylesheet toe op de QApplication.

    Moet worden aangeroepen ná `QApplication(sys.argv)` en vóór constructie van
    het hoofdvenster, zodat alle widgets vanaf het begin de juiste styling krijgen.

    Parameters
    ----------
    actief_thema_naam:
        Naam van het thema (bv. 'DKIB'). Verwijst naar `themes/<naam>.json`
        (case-insensitief gematched op bestandsnaam).

    Returns
    -------
    Theme | None
        Het geladen thema-object; `None` als geen enkel thema geladen kon worden
        (in dat geval blijft de Qt-default stylesheet actief).
    """
    thema = _laad_thema_met_fallback(actief_thema_naam)
    if thema is None:
        return None

    werkelijke_familie = _registreer_fonts(thema.assets.font_files,
                                           fallback=thema.typography.fallback)

    qss = thema.build_stylesheet(font_family=werkelijke_familie)
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(qss)

    return thema


def _laad_thema_met_fallback(naam: str) -> Theme | None:
    """Probeer het gewenste thema te laden; val terug op DKIB; daarna op niets."""
    kandidaten = [naam]
    if naam.lower() != DEFAULT_THEME.lower():
        kandidaten.append(DEFAULT_THEME)

    for kandidaat in kandidaten:
        pad = _vind_thema_bestand(kandidaat)
        if pad is None:
            continue
        try:
            return Theme.load(pad)
        except (ValueError, OSError) as exc:
            print(f'Waarschuwing: thema {kandidaat!r} kon niet geladen worden: {exc}',
                  file=sys.stderr)
    return None


def _vind_thema_bestand(naam: str) -> Path | None:
    """Zoek `<themes_dir>/<naam>.json` (case-insensitief)."""
    if not THEMES_DIR.exists():
        return None
    doel = naam.lower()
    for pad in THEMES_DIR.glob('*.json'):
        if pad.stem.lower() == doel:
            return pad
    return None


def _registreer_fonts(font_paden: list[str], fallback: str) -> str:
    """Registreer fonts via QFontDatabase en geef de werkelijke familienaam terug.

    Parameters
    ----------
    font_paden:
        Lijst van absolute paden naar `.ttf`-bestanden.
    fallback:
        Familienaam om terug te vallen wanneer geen enkele font geladen kon worden.

    Returns
    -------
    str
        De werkelijke font-familienaam zoals door Qt gerapporteerd, of `fallback`
        wanneer geen enkele font succesvol is geregistreerd.
    """
    werkelijke_naam: str | None = None
    for pad in font_paden:
        font_id = QFontDatabase.addApplicationFont(pad)
        if font_id == -1:
            print(f'Waarschuwing: kon font niet laden: {pad}', file=sys.stderr)
            continue
        if werkelijke_naam is None:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                werkelijke_naam = families[0]

    return werkelijke_naam or fallback
```

- [ ] **Stap 2: Smoke-test — bestand kan worden geïmporteerd**

```bash
python -c "from app.theme_apply import bootstrap_theme; print('ok')"
```

Verwacht: `ok`.

- [ ] **Stap 3: Commit**

```bash
git add app/theme_apply.py
git commit -m "feat: voeg theme_apply bootstrap toe (Qt-aware)"
```

---

## Task 7: Bedraad bootstrap in `run.pyw` en geef Theme door aan `MainWindow`

**Files:**
- Modify: `run.pyw:42-53`
- Modify: `app/main_window.py:101-132`

- [ ] **Stap 1: Pas `run.pyw` aan**

Vervang in `run.pyw` regels 42-53:

```python
from app.config_manager import ConfigManager
from app.main_window import MainWindow
from app.theme_apply import bootstrap_theme


def main() -> None:
    """Start de D-Sheet Dashboard applicatie."""
    app = QApplication(sys.argv)
    app.setApplicationName('D-Sheet Dashboard')
    app.setOrganizationName('DKIB Geotechniek')

    # Lees actief-thema-naam uit config (default 'DKIB' bij ontbreken)
    _, _, app_settings = ConfigManager().load()
    thema = bootstrap_theme(app_settings.active_theme_name)

    window = MainWindow(thema=thema)
    window.show()
    sys.exit(app.exec())
```

- [ ] **Stap 2: Pas `MainWindow.__init__` aan om thema-parameter te ontvangen**

In `app/main_window.py`, vervang de bestaande `__init__`-handtekening en bovenste regels:

```python
    def __init__(self, thema=None):
        """Initialiseer het hoofdvenster.

        Parameters
        ----------
        thema:
            Het actieve `Theme`-object voor branding-elementen (zoals app-logo).
            Mag `None` zijn — branding-elementen worden dan weggelaten.
        """
        super().__init__()
        self.setWindowTitle('D-Sheet Dashboard')
        self.resize(1600, 950)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)

        self._theme = thema

        self._state = AppState()
```

(De bestaande regels onder `self._state = AppState()` blijven ongewijzigd.)

Voeg bovenaan `app/main_window.py` (na de andere imports) toe:

```python
from app.theme import Theme  # noqa: F401  (gebruikt voor type-annotatie hint)
```

En pas de annotatie aan:

```python
    def __init__(self, thema: Theme | None = None) -> None:
```

- [ ] **Stap 3: Smoke-test — app start nog**

```bash
python run.pyw &
sleep 3
# Sluit het venster handmatig of:
# tasklist | grep -i python
```

Verwacht: het hoofdvenster opent zonder crash. De UI ziet er nu al licht anders uit (het thema is actief op alle Qt-widgets) — knoppen die in andere tabs nog `_BTN_PRIMARY`-inline gebruiken behouden hun huidige inline-styling.

- [ ] **Stap 4: Commit**

```bash
git add run.pyw app/main_window.py
git commit -m "feat: bedraad bootstrap_theme in run.pyw en geef Theme door aan MainWindow"
```

---

## Task 8: Voeg TopLeft cornerwidget toe met thema-app-logo

**Files:**
- Modify: `app/main_window.py:155-227`

- [ ] **Stap 1: Voeg helper-methode toe in `MainWindow`**

In `app/main_window.py`, voeg vlak voor `_build_project_corner` toe:

```python
    def _build_branding_corner(self) -> 'QWidget | None':
        """Logo-cornerwidget linksboven in de tabbalk.

        Returns
        -------
        QWidget | None
            Een QLabel met het thema-app-logo, of `None` als er geen logo is
            of als het bestand niet geladen kan worden.
        """
        if self._theme is None or not self._theme.assets.app_logo:
            return None

        from PyQt6.QtGui import QPixmap
        pix = QPixmap(self._theme.assets.app_logo)
        if pix.isNull():
            return None

        pix = pix.scaledToHeight(
            28, Qt.TransformationMode.SmoothTransformation
        )
        label = QLabel()
        label.setPixmap(pix)
        label.setContentsMargins(8, 2, 8, 2)
        return label
```

- [ ] **Stap 2: Roep de helper aan in `_build_ui`**

In `_build_ui`, vlak na `self._main_tabs.setDocumentMode(False)` en vóór `self._main_tabs.setCornerWidget(self._build_project_corner(), Qt.Corner.TopRightCorner)`, voeg toe:

```python
        # Branding cornerwidget linksboven (alleen als thema en logo aanwezig)
        branding = self._build_branding_corner()
        if branding is not None:
            self._main_tabs.setCornerWidget(branding, Qt.Corner.TopLeftCorner)
```

- [ ] **Stap 3: Vervang inline `_BTN_PRIMARY` op de export-knop door `objectName`**

In `_build_project_corner`, vervang:

```python
        self._btn_export_rapport = QPushButton('Exporteer rapport (Word)')
        self._btn_export_rapport.setStyleSheet(_BTN_PRIMARY)
        self._btn_export_rapport.setEnabled(False)
        layout.addWidget(self._btn_export_rapport)
```

door:

```python
        self._btn_export_rapport = QPushButton('Exporteer rapport (Word)')
        self._btn_export_rapport.setObjectName('btnPrimary')
        self._btn_export_rapport.setEnabled(False)
        layout.addWidget(self._btn_export_rapport)
```

En vervang in dezelfde methode:

```python
        lbl = QLabel('Project:')
        lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #2c3e50;')
        layout.addWidget(lbl)
```

door:

```python
        lbl = QLabel('Project:')
        lbl.setObjectName('projectLabel')
        layout.addWidget(lbl)
```

- [ ] **Stap 4: Smoke-test — app start, DKIB-logo zichtbaar linksboven**

```bash
python run.pyw
```

Verifieer:
- DKIB-logo verschijnt klein linksboven in de tabbalk
- "Exporteer rapport"-knop heeft het nieuwe heldere DKIB-blauw `#147ACF`
- Andere tabs zien er nog ongewijzigd uit (hun lokale stylesheets domineren)
- "Project:"-label naast de dropdown is in de juiste tekstkleur

Sluit de app.

- [ ] **Stap 5: Commit**

```bash
git add app/main_window.py
git commit -m "feat: toon thema-logo linksboven en thematiseer export-knop"
```

---

## Task 9: Refactor `tab_report_context.py` — gebruik objectNames

**Files:**
- Modify: `ui/tabs/tab_report_context.py:19-30` (verwijder constants)
- Modify: `ui/tabs/tab_report_context.py:114-129` (knoppen)

- [ ] **Stap 1: Verwijder lokale stijlconstanten**

In `ui/tabs/tab_report_context.py`, **verwijder** regels 19-30 (de `_BTN_PRIMARY` en `_BTN_DANGER` definities). De file gaat dan direct van `_LOGO_DISPLAY_HEIGHT = 80` naar `class TabReportContext`.

- [ ] **Stap 2: Vervang `setStyleSheet`-aanroepen door `setObjectName`**

In dezelfde file, vervang:

```python
        self.import_btn = QPushButton('Importeer…')
        self.import_btn.setStyleSheet(_BTN_PRIMARY)
        self.import_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.import_btn)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.setStyleSheet(_BTN_DANGER)
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.reset_btn)

        self.remove_btn = QPushButton('Verwijder project')
        self.remove_btn.setStyleSheet(_BTN_DANGER)
        self.remove_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        import_layout.addWidget(self.remove_btn)
```

door:

```python
        self.import_btn = QPushButton('Importeer…')
        self.import_btn.setObjectName('btnPrimary')
        self.import_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.import_btn)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.setObjectName('btnDanger')
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.reset_btn)

        self.remove_btn = QPushButton('Verwijder project')
        self.remove_btn.setObjectName('btnDanger')
        self.remove_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        import_layout.addWidget(self.remove_btn)
```

- [ ] **Stap 3: Voeg `objectName` toe aan de bladeren/wissen-knoppen**

In dezelfde file, vervang:

```python
        btn_row = QHBoxLayout()
        self._btn_browse = QPushButton('Bladeren…')
        self._btn_browse.clicked.connect(self._browse_logo)
        self._btn_clear = QPushButton('Wissen')
        self._btn_clear.clicked.connect(self._clear_logo)
        btn_row.addWidget(self._btn_browse)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        logo_layout.addLayout(btn_row)
```

door:

```python
        btn_row = QHBoxLayout()
        self._btn_browse = QPushButton('Bladeren…')
        self._btn_browse.setObjectName('btnNormal')
        self._btn_browse.clicked.connect(self._browse_logo)
        self._btn_clear = QPushButton('Wissen')
        self._btn_clear.setObjectName('btnNormal')
        self._btn_clear.clicked.connect(self._clear_logo)
        btn_row.addWidget(self._btn_browse)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        logo_layout.addLayout(btn_row)
```

- [ ] **Stap 4: Smoke-test — Tab Rapportcontext heeft nieuwe stijl**

```bash
python run.pyw
```

Verifieer:
- "Importeer…" is helder DKIB-blauw `#147ACF`
- "Reset" en "Verwijder project" zijn rood-gerand op witte achtergrond
- "Bladeren…" en "Wissen" hebben de neutrale knop-stijl met grijze rand
- GroupBox-titels ("Rapportgegevens", "Logo", "Status", "Ingeladen projecten") zijn DKIB-blauw en bold
- Andere tabs blijven ongewijzigd

Sluit de app.

- [ ] **Stap 5: Run pytest om regressies te vangen**

```bash
pytest tests/ -v
```

Verwacht: alle tests slagen.

- [ ] **Stap 6: Commit**

```bash
git add ui/tabs/tab_report_context.py
git commit -m "refactor: gebruik objectNames in TabReportContext (pilot thema-systeem)"
```

---

## Task 10: Refactor `tab_instellingen.py` — Template-groep + objectNames

**Files:**
- Modify: `ui/tabs/tab_instellingen.py` (volledig)

- [ ] **Stap 1: Voeg signal toe en verwijder lokale stijlconstanten**

Vervang in `ui/tabs/tab_instellingen.py` regels 1-31:

```python
"""Tab Instellingen — persistente app-instellingen, template-keuze en preview-opener."""

from __future__ import annotations
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QComboBox,
)
from PyQt6.QtCore import pyqtSignal


class TabInstellingen(QWidget):
    """Tabblad met persistente applicatie-instellingen (Tab Instellingen)."""

    template_path_changed = pyqtSignal(str)
    """Afgegeven zodra het Word-template-pad wijzigt (ook bij wissen)."""

    import_map_changed = pyqtSignal(str)
    """Afgegeven zodra de standaard importmap wijzigt (ook bij wissen)."""

    theme_selected = pyqtSignal(str)
    """Afgegeven zodra de gebruiker op 'Toepassen' klikt voor een ander UI-thema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._huidig_thema_naam: str = ''
        self._beschikbare_themas: list[tuple[str, Path]] = []
        self._build()
```

- [ ] **Stap 2: Voeg `_build_template_group` toe en pas `_build` aan**

Vervang in dezelfde file de hele `_build`-methode:

```python
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Groep: Template (UI-thema) ────────────────────────────────
        root.addWidget(self._build_template_group())

        # ── Groep: Rapportage-instellingen ────────────────────────────
        tmpl_box = QGroupBox('Rapportage-instellingen')
        tmpl_vl = QVBoxLayout(tmpl_box)
        tmpl_vl.setSpacing(6)

        lbl = QLabel('Word-template (.dotx)')
        lbl.setObjectName('hintLabel')

        tmpl_rij = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .dotx template… (optioneel)')
        self._template_edit.textChanged.connect(self.template_path_changed)

        bladeren_btn = QPushButton('Bladeren…')
        bladeren_btn.setObjectName('btnNormal')
        bladeren_btn.clicked.connect(self._on_bladeren)

        wis_btn = QPushButton('✕')
        wis_btn.setObjectName('btnClear')
        wis_btn.setFixedWidth(28)
        wis_btn.setToolTip('Verwijder template-pad')
        wis_btn.clicked.connect(self._on_wis_template)

        tmpl_rij.addWidget(self._template_edit)
        tmpl_rij.addWidget(bladeren_btn)
        tmpl_rij.addWidget(wis_btn)

        hint = QLabel(
            'Optioneel — wordt ook gebruikt bij Word-export als het export-venster leeg is'
        )
        hint.setObjectName('hintLabel')

        tmpl_vl.addWidget(lbl)
        tmpl_vl.addLayout(tmpl_rij)
        tmpl_vl.addWidget(hint)
        root.addWidget(tmpl_box)

        # ── Groep: Import-instellingen ────────────────────────────────
        imp_box = QGroupBox('Import-instellingen')
        imp_vl = QVBoxLayout(imp_box)
        imp_vl.setSpacing(6)

        imp_lbl = QLabel('Standaard importmap')
        imp_lbl.setObjectName('hintLabel')

        imp_rij = QHBoxLayout()
        self._import_map_edit = QLineEdit()
        self._import_map_edit.setPlaceholderText('Map om import-dialoog in te openen… (optioneel)')
        self._import_map_edit.textChanged.connect(self.import_map_changed)

        imp_bladeren_btn = QPushButton('Bladeren…')
        imp_bladeren_btn.setObjectName('btnNormal')
        imp_bladeren_btn.clicked.connect(self._on_bladeren_importmap)

        imp_wis_btn = QPushButton('✕')
        imp_wis_btn.setObjectName('btnClear')
        imp_wis_btn.setFixedWidth(28)
        imp_wis_btn.setToolTip('Verwijder standaard importmap')
        imp_wis_btn.clicked.connect(self._on_wis_importmap)

        imp_rij.addWidget(self._import_map_edit)
        imp_rij.addWidget(imp_bladeren_btn)
        imp_rij.addWidget(imp_wis_btn)

        imp_hint = QLabel('Het importeer-dialoogvenster opent voortaan in deze map')
        imp_hint.setObjectName('hintLabel')

        imp_vl.addWidget(imp_lbl)
        imp_vl.addLayout(imp_rij)
        imp_vl.addWidget(imp_hint)
        root.addWidget(imp_box)

        root.addStretch()

    def _build_template_group(self) -> QGroupBox:
        """Bouw de Template-groep (UI-thema-keuze)."""
        box = QGroupBox('Template (UI-thema)')
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        self._actief_label = QLabel('Actief: -')
        self._actief_label.setObjectName('hintLabel')
        vl.addWidget(self._actief_label)

        rij = QHBoxLayout()
        self._theme_combo = QComboBox()
        self._theme_combo.setMinimumWidth(220)
        rij.addWidget(self._theme_combo)

        self._theme_apply_btn = QPushButton('Toepassen')
        self._theme_apply_btn.setObjectName('btnPrimary')
        self._theme_apply_btn.clicked.connect(self._on_theme_apply)
        rij.addWidget(self._theme_apply_btn)
        rij.addStretch()
        vl.addLayout(rij)

        self._herstart_label = QLabel('Wisseling actief na herstart van de app.')
        self._herstart_label.setObjectName('hintLabel')
        self._herstart_label.setVisible(False)
        vl.addWidget(self._herstart_label)

        return box
```

- [ ] **Stap 3: Voeg publieke API en handlers toe**

Vervang in dezelfde file de gehele `# Publieke API` en `# Privé handlers` secties (vanaf regel met `def set_import_map`) door:

```python
    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_import_map(self, pad: str) -> None:
        """Toon een opgeslagen importmap zonder een signal af te geven."""
        self._import_map_edit.blockSignals(True)
        self._import_map_edit.setText(pad)
        self._import_map_edit.blockSignals(False)

    def set_template_path(self, pad: str) -> None:
        """Toon een opgeslagen template-pad zonder een signal af te geven."""
        self._template_edit.blockSignals(True)
        self._template_edit.setText(pad)
        self._template_edit.blockSignals(False)

    def set_themes(self, themas: list[tuple[str, Path]], actief_naam: str) -> None:
        """Vul de thema-dropdown en markeer het huidige actieve thema.

        Parameters
        ----------
        themas:
            Lijst van (naam, pad)-paren zoals teruggegeven door `discover_themes()`.
        actief_naam:
            Naam van het thema dat momenteel actief is (verschijnt in 'Actief: …').
        """
        self._beschikbare_themas = themas
        self._huidig_thema_naam = actief_naam
        self._actief_label.setText(f'Actief: {actief_naam or "-"}')

        self._theme_combo.blockSignals(True)
        self._theme_combo.clear()
        idx_actief = -1
        for i, (naam, _pad) in enumerate(themas):
            self._theme_combo.addItem(naam)
            if naam == actief_naam:
                idx_actief = i
        if idx_actief >= 0:
            self._theme_combo.setCurrentIndex(idx_actief)
        self._theme_combo.blockSignals(False)

        self._herstart_label.setVisible(False)

    # ------------------------------------------------------------------
    # Privé handlers
    # ------------------------------------------------------------------

    def _on_bladeren(self) -> None:
        pad, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer Word-template', '', 'Word-sjabloon (*.dotx);;Word (*.docx)'
        )
        if pad:
            self._template_edit.setText(pad)

    def _on_wis_template(self) -> None:
        self._template_edit.clear()

    def _on_bladeren_importmap(self) -> None:
        map_pad = QFileDialog.getExistingDirectory(
            self, 'Selecteer standaard importmap',
            self._import_map_edit.text() or '',
        )
        if map_pad:
            self._import_map_edit.setText(map_pad)

    def _on_wis_importmap(self) -> None:
        self._import_map_edit.clear()

    def _on_theme_apply(self) -> None:
        """Gebruiker klikt 'Toepassen' op de thema-dropdown."""
        gekozen = self._theme_combo.currentText()
        if not gekozen or gekozen == self._huidig_thema_naam:
            return
        self._herstart_label.setVisible(True)
        self.theme_selected.emit(gekozen)
```

- [ ] **Stap 4: Smoke-test — Tab Instellingen werkt en heeft Template-groep**

```bash
python run.pyw
```

Verifieer:
- Tab Instellingen toont nu een "Template (UI-thema)"-groep bovenaan (nog leeg — wordt in Task 11 gevuld)
- "Bladeren…" en "✕" knoppen hebben de nieuwe DKIB-stijl
- "Rapportage-instellingen" en "Import-instellingen" werken nog steeds (paden invoeren/wissen)

Sluit de app.

- [ ] **Stap 5: Commit**

```bash
git add ui/tabs/tab_instellingen.py
git commit -m "refactor: gebruik objectNames in TabInstellingen en voeg Template-groep toe"
```

---

## Task 11: Bedraad thema-keuze in `MainWindow` → `ConfigManager`

**Files:**
- Modify: `app/main_window.py` (`__init__`, `_connect_signals`, nieuwe handler)

- [ ] **Stap 1: Voeg theme-imports toe**

Bovenaan `app/main_window.py`, in het lokale-imports blok, voeg toe:

```python
from app.theme import discover_themes
from app.theme_apply import THEMES_DIR
```

- [ ] **Stap 2: Vul de thema-dropdown bij opstarten**

In `MainWindow.__init__`, na de regel `self._sync_render_spinboxes(self._state.render_settings)` (regel ~127), voeg toe:

```python
        # Vul thema-dropdown in Instellingen-tab
        themas = discover_themes(THEMES_DIR)
        actief = self._state.app_settings.active_theme_name
        self._tab_instellingen.set_themes(themas, actief)
```

- [ ] **Stap 3: Verbind `theme_selected`-signal**

In `_connect_signals`, na de regel `self._tab_instellingen.import_map_changed.connect(self._on_import_map_changed)`, voeg toe:

```python
        self._tab_instellingen.theme_selected.connect(self._on_theme_selected)
```

- [ ] **Stap 4: Voeg de handler toe**

In `app/main_window.py`, vlak na `_on_import_map_changed`, voeg toe:

```python
    def _on_theme_selected(self, naam: str) -> None:
        """Sla nieuw gekozen thema op in config; herstart vereist."""
        huidig = self._state.app_settings
        self._controller.apply_app_settings(AppSettings(
            word_template_path=huidig.word_template_path,
            standaard_importmap=huidig.standaard_importmap,
            active_theme_name=naam,
        ))
```

- [ ] **Stap 5: Smoke-test — kies SixGeoConsult, herstart, zie ander thema**

```bash
python run.pyw
```

1. Ga naar tab "Instellingen"
2. Selecteer "SixGeoConsult" in de Template-dropdown
3. Klik "Toepassen" — zie info-tekst "Wisseling actief na herstart van de app."
4. Sluit de app
5. Start opnieuw: `python run.pyw`
6. Verifieer: knoppen zijn nu paars (`#7a4f9f`) i.p.v. blauw, app-logo in cornerwidget is SIXGeoConsult
7. Ga terug naar Instellingen, kies "DKIB", klik Toepassen, sluit, herstart
8. Verifieer: terug naar DKIB-blauw

- [ ] **Stap 6: Commit**

```bash
git add app/main_window.py
git commit -m "feat: bedraad thema-keuze in MainWindow met persistentie"
```

---

## Task 12: Visuele eindcheck en regressietest

**Files:** geen (alleen verifiëren)

- [ ] **Stap 1: Run alle tests**

```bash
pytest tests/ -v
```

Verwacht: alle tests slagen, inclusief de nieuwe `test_theme.py` en `test_app_settings_theme.py`.

- [ ] **Stap 2: Visuele controle van Tab Rapportcontext**

```bash
python run.pyw
```

Controleer op tab "Rapportcontext":
- DKIB-logo klein zichtbaar linksboven in tabbalk
- Tabnaam "Rapportcontext" met DKIB-blauwe top-border, geen dubbele lijn met de pane
- "Importeer…" knop heeft helder `#147ACF` blauw
- "Reset" en "Verwijder project" knoppen zijn rood-gerand op wit
- "Bladeren…" en "Wissen" knoppen zijn neutraal-grijs
- GroupBox-titels ("Rapportgegevens", "Logo", "Status", "Ingeladen projecten") in DKIB-blauw
- Tekstvelden hebben dunne grijze randen met radius 4

- [ ] **Stap 3: Visuele controle van Tab Instellingen**

Op tab "Instellingen":
- "Template (UI-thema)" groep bovenaan met DKIB-blauwe titel
- Dropdown bevat "DKIB" en "SixGeoConsult"
- "Actief: DKIB" zichtbaar
- "Toepassen"-knop is DKIB-blauw
- Andere groepen ("Rapportage-instellingen", "Import-instellingen") werken normaal

- [ ] **Stap 4: Visuele controle dat andere tabs niet kapot zijn**

Klik door alle andere tabs (Doorsnede, Resultaten, etc.). Verifieer:
- Geen visuele glitches (zwarte vlakken, verdwenen widgets)
- Functionaliteit werkt: importeer een test-bestand, navigeer fases, exporteer PNG
- De andere tabs kunnen er stilistisch nog "oud" uitzien (lokale `_BTN_PRIMARY` etc. is niet aangeraakt) — dat is opzettelijk, scope van pilot

- [ ] **Stap 5: Geen wijzigingen, geen commit nodig**

Als alles werkt: pilot is klaar. Andere tabs migreren naar het thema-systeem is een vervolgkwestie.

Als visuele bug: bug oplossen in een nieuwe commit met message `fix: <beschrijving>`.

---

## Out of scope reminder

Deze tabs zijn **bewust niet** aangepast in deze ronde — hun lokale `_BTN_PRIMARY`/`_BTN_NORMAL` constanten staan nog in plaats:

- Doorsnede (Tab 1)
- Grondsoortentabel (Tab 2B)
- Invoerbeschrijving (Tab 2C)
- Resultaten (Tab 3A)
- Resultaatbeschrijving (Tab 3B)
- Rapportageselectie (Tab 4A)
- Export (Tab 4B)
- Aanvullende berekeningen (Tab 5)
- Debug

Hun migratie volgt in vervolgrondes (één tab per ronde, of alle in één opruim-PR — beslissing voor later).

Ook niet in deze ronde:
- Matplotlib chart-kleuren afgestemd op het thema
- Word/Excel template-pad gekoppeld aan UI-thema
- Live theme-switch zonder herstart
