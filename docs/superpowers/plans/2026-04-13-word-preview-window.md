# Word Preview Window — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Een zwevend HTML-preview venster dat automatisch de geselecteerde rapportsecties toont naast de hoofdapplicatie, gekoppeld aan een persistent Word-template-pad via een nieuw Instellingen-tabje.

**Architecture:** `HtmlPreviewBuilder` genereert een HTML-string uit `ReportPackage`; `WordPreviewWindow(QMainWindow)` toont deze in een `QTextBrowser`; `TabInstellingen` beheert het template-pad en de "Preview openen" knop. `_update_all()` in `MainWindow` triggert de preview automatisch als het venster open is. `AppSettings` dataclass persisteert de configuratie via `ConfigManager`.

**Tech Stack:** Python 3.10+, PyQt6, python-docx (optioneel), pytest

---

## Bestandsoverzicht

| Actie | Bestand | Verantwoordelijkheid |
|---|---|---|
| Aanmaken | `reporting/builders/html_preview_builder.py` | HTML genereren uit `ReportPackage` |
| Aanmaken | `ui/preview_window.py` | Zwevend preview-venster |
| Aanmaken | `ui/tabs/tab_instellingen.py` | Instellingen-tabje met template-pad + preview-knop |
| Aanmaken | `tests/test_app_settings.py` | Tests voor config round-trip |
| Aanmaken | `tests/test_html_preview_builder.py` | Tests voor HTML-uitvoer |
| Wijzigen | `app/settings.py` | `AppSettings` dataclass toevoegen |
| Wijzigen | `app/config_manager.py` | `AppSettings` laden/opslaan; testbaar via optioneel pad |
| Wijzigen | `app/state.py` | `app_settings: AppSettings` veld |
| Wijzigen | `app/controller.py` | `load_config()`, `save_config()`, `apply_app_settings()` |
| Wijzigen | `app/main_window.py` | Tab + venster toevoegen, signalen koppelen, `_update_all()` uitbreiden |
| Wijzigen | `app/report_controller.py` | Fallback template-pad in `export_word()` |

---

## Task 1: AppSettings dataclass + ConfigManager uitbreiding

**Files:**
- Modify: `app/settings.py`
- Modify: `app/config_manager.py`
- Modify: `app/state.py`
- Modify: `app/controller.py`
- Create: `tests/test_app_settings.py`

- [ ] **Stap 1: Schrijf de falende tests**

Maak `tests/test_app_settings.py` aan:

```python
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
```

- [ ] **Stap 2: Voer tests uit — verwacht FAIL**

```bash
pytest tests/test_app_settings.py -v
```

Verwacht: `ImportError: cannot import name 'AppSettings'`

- [ ] **Stap 3: Voeg `AppSettings` toe aan `app/settings.py`**

Voeg onderaan het bestaande bestand toe (na `ViewportSettings`):

```python
@dataclass
class AppSettings:
    """Algemene applicatie-instellingen."""
    word_template_path: str = ''
    """Pad naar het Word-template (.docx); leeg = geen template."""
```

- [ ] **Stap 4: Pas `app/config_manager.py` aan**

Vervang de volledige inhoud van `app/config_manager.py`:

```python
"""Configuratiepersistentie voor D-Sheet Dashboard."""

from __future__ import annotations
import json
from pathlib import Path

from app.settings import RenderSettings, ViewportSettings, AppSettings

CONFIG_DIR = Path.home() / '.dsheet_dashboard'
CONFIG_FILE = CONFIG_DIR / 'config.json'


class ConfigManager:
    """Beheert het lezen en schrijven van de gebruikersconfiguratie."""

    def __init__(self, config_file: Path | None = None) -> None:
        self._config_file = config_file or CONFIG_FILE
        self._config_dir = self._config_file.parent

    def load(self) -> tuple[RenderSettings, ViewportSettings, AppSettings]:
        """Lees config.json; geef defaults terug bij ontbreken of fouten."""
        if not self._config_file.exists():
            return RenderSettings(), ViewportSettings(), AppSettings()
        try:
            with open(self._config_file, encoding='utf-8') as f:
                cfg = json.load(f)
            rs_data = cfg.get('render_settings', {})
            vp_data = cfg.get('viewport_settings', {})
            app_data = cfg.get('app_settings', {})
            rs = RenderSettings(**{
                k: v for k, v in rs_data.items()
                if k in RenderSettings.__dataclass_fields__
            }) if rs_data else RenderSettings()
            vp = ViewportSettings(**{
                k: v for k, v in vp_data.items()
                if k in ViewportSettings.__dataclass_fields__
            }) if vp_data else ViewportSettings()
            app = AppSettings(**{
                k: v for k, v in app_data.items()
                if k in AppSettings.__dataclass_fields__
            }) if app_data else AppSettings()
            return rs, vp, app
        except Exception:
            return RenderSettings(), ViewportSettings(), AppSettings()

    def save(self, rs: RenderSettings, vp: ViewportSettings,
             app: AppSettings | None = None) -> None:
        """Sla render-, viewport- en app-instellingen op naar config.json."""
        if app is None:
            app = AppSettings()
        self._config_dir.mkdir(parents=True, exist_ok=True)
        cfg = {
            'render_settings': {f: getattr(rs, f) for f in rs.__dataclass_fields__},
            'viewport_settings': {f: getattr(vp, f) for f in vp.__dataclass_fields__},
            'app_settings': {f: getattr(app, f) for f in app.__dataclass_fields__},
        }
        with open(self._config_file, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
```

- [ ] **Stap 5: Voeg `app_settings` toe aan `app/state.py`**

Voeg de import van `AppSettings` toe aan de bestaande import-regel:

```python
from app.settings import RenderSettings, ViewportSettings, AppSettings
```

Voeg het veld toe na `viewport_settings` in de `AppState`-dataclass:

```python
    app_settings: AppSettings = field(default_factory=AppSettings)
    """Algemene applicatie-instellingen (template-pad, etc.)."""
```

- [ ] **Stap 6: Pas `app/controller.py` aan**

Voeg `AppSettings` toe aan de import-regel bovenaan:

```python
from app.settings import RenderSettings, ViewportSettings, AppSettings
```

Vervang de bestaande `load_config()` en `save_config()` methoden en voeg `apply_app_settings()` toe:

```python
    def load_config(self) -> None:
        """Lees config.json en pas toe op state."""
        rs, vp, app = self._config.load()
        self._state.render_settings = rs
        self._state.viewport_settings = vp
        self._state.app_settings = app

    def save_config(self) -> None:
        """Sla huidige instellingen op."""
        self._config.save(
            self._state.render_settings,
            self._state.viewport_settings,
            self._state.app_settings,
        )

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Sla nieuwe app-instellingen op in state en config.

        Parameters
        ----------
        settings:
            Nieuw AppSettings-object met de gewenste waarden.
        """
        self._state.app_settings = settings
        self._config.save(
            self._state.render_settings,
            self._state.viewport_settings,
            settings,
        )
```

- [ ] **Stap 7: Voer tests uit — verwacht PASS**

```bash
pytest tests/test_app_settings.py -v
```

Verwacht: 3 × PASSED

- [ ] **Stap 8: Bestaande tests nog steeds groen**

```bash
pytest tests/test_parsers.py -v
```

Verwacht: alle tests PASSED

- [ ] **Stap 9: Commit**

```bash
git add app/settings.py app/config_manager.py app/state.py app/controller.py tests/test_app_settings.py
git commit -m "feat: voeg AppSettings toe met persistentie via ConfigManager"
```

---

## Task 2: HtmlPreviewBuilder

**Files:**
- Create: `reporting/builders/html_preview_builder.py`
- Create: `tests/test_html_preview_builder.py`

- [ ] **Stap 1: Schrijf de falende tests**

Maak `tests/test_html_preview_builder.py` aan:

```python
"""Tests voor HtmlPreviewBuilder."""

from __future__ import annotations

from reporting.builders.html_preview_builder import HtmlPreviewBuilder
from reporting.models import (
    ReportPackage, ReportMetadata, ReportSection,
    ReportField, ReportTable, ReportItem, TextBlock,
)


def _maak_package_met_sectie() -> tuple[ReportPackage, ReportSection]:
    sec = ReportSection(id='damwand', title='Damwand')
    sec.fields.append(ReportField('top', 'Bovenzijde', '0,00', 'm NAP'))
    sec.fields.append(ReportField('bot', 'Onderzijde', '-12,50', 'm NAP'))
    item = ReportItem(
        id='input_damwand', kind='invoer', caption='Damwand', source_ref='damwand'
    )
    pkg = ReportPackage(
        metadata=ReportMetadata(project_name='Testproject'),
        input_sections=[sec],
        selected_items=[item],
    )
    return pkg, sec


def test_lege_package_bevat_geen_secties_melding() -> None:
    """Lege package → melding 'Geen secties geselecteerd'."""
    html = HtmlPreviewBuilder().build(ReportPackage())
    assert 'Geen secties geselecteerd' in html


def test_projectnaam_zichtbaar_in_html() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Testproject' in html


def test_geselecteerde_sectietitel_zichtbaar() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Damwand' in html


def test_velden_zichtbaar_in_html() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Bovenzijde' in html
    assert '0,00' in html
    assert 'm NAP' in html


def test_niet_geselecteerde_sectie_niet_zichtbaar() -> None:
    sec = ReportSection(id='water', title='Waterpeilen')
    pkg = ReportPackage(input_sections=[sec], selected_items=[])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Waterpeilen' not in html


def test_tabel_weergegeven_als_html_tabel() -> None:
    tbl = ReportTable(
        id='ankers', title='Ankers',
        columns=['Naam', 'Niveau [m NAP]'],
        rows=[['Anker-1', '-3,50'], ['Anker-2', '-4,00']],
    )
    sec = ReportSection(id='anchors', title='Ankers', tables=[tbl])
    item = ReportItem(id='input_anchors', kind='invoer', caption='Ankers', source_ref='anchors')
    pkg = ReportPackage(input_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert '<table' in html.lower()
    assert 'Anker-1' in html
    assert '-3,50' in html


def test_tekstblok_effective_text_zichtbaar() -> None:
    sec = ReportSection(id='sec', title='Sectie')
    sec.text_blocks.append(TextBlock(
        id='blk', section='sec',
        generated_text='Gegenereerde tekst.',
        manual_override='Handmatige override.',
    ))
    item = ReportItem(id='input_sec', kind='invoer', caption='Sectie', source_ref='sec')
    pkg = ReportPackage(input_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Handmatige override.' in html
    assert 'Gegenereerde tekst.' not in html


def test_resultaat_sectie_opgenomen_bij_kind_resultaat() -> None:
    sec = ReportSection(id='moment', title='Momentendiagram')
    sec.fields.append(ReportField('max', 'Max. moment', '142,3', 'kNm/m'))
    item = ReportItem(
        id='result_moment', kind='resultaat', caption='Momenten', source_ref='moment'
    )
    pkg = ReportPackage(result_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Momentendiagram' in html
    assert '142,3' in html
```

- [ ] **Stap 2: Voer tests uit — verwacht FAIL**

```bash
pytest tests/test_html_preview_builder.py -v
```

Verwacht: `ImportError: No module named 'reporting.builders.html_preview_builder'`

- [ ] **Stap 3: Implementeer `HtmlPreviewBuilder`**

Maak `reporting/builders/html_preview_builder.py` aan:

```python
"""HtmlPreviewBuilder — genereert een HTML-string uit een ReportPackage."""

from __future__ import annotations

from reporting.models import ReportPackage, ReportSection, ReportField, ReportTable

# ── Kleurconstanten (consistent met app-stijl) ───────────────────────────────
_HDR_BG   = '#1b3a5c'
_HDR_FG   = '#ffffff'
_SUB_BG   = '#274f77'
_SUB_FG   = '#d0e8f5'
_ODD_BG   = '#f3f8fc'
_EVEN_BG  = '#ffffff'
_SEP      = '#dce8f0'
_LABEL    = '#2c3f52'
_VALUE    = '#0f1e2b'
_FONT     = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'

_CSS = f"""
  body {{ font-family: {_FONT}; font-size: 12px; color: {_VALUE};
          margin: 0; padding: 16px; background: #ffffff; }}
  h1   {{ font-size: 15px; font-weight: 700; color: {_HDR_BG};
          border-bottom: 2px solid {_HDR_BG}; padding-bottom: 6px;
          margin-bottom: 16px; }}
  h2   {{ font-size: 12px; font-weight: 700; color: {_SUB_BG};
          margin: 18px 0 6px 0; padding: 5px 10px;
          background: #eaf2f8; border-left: 3px solid {_SUB_BG}; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
  th    {{ background: {_HDR_BG}; color: {_HDR_FG}; font-size: 11px;
           font-weight: 600; padding: 5px 10px; text-align: left; }}
  td    {{ padding: 5px 10px; border-bottom: 1px solid {_SEP};
           font-size: 11px; }}
  tr.odd  td {{ background: {_ODD_BG}; }}
  tr.even td {{ background: {_EVEN_BG}; }}
  td.label {{ color: {_LABEL}; font-weight: 500; width: 45%; }}
  td.value {{ text-align: right; }}
  td.unit  {{ color: #5a7a8a; font-size: 10px; width: 20%; }}
  p.tekst  {{ font-size: 11px; color: #3d4f5c; margin: 4px 0 10px 0;
              line-height: 1.6; }}
  p.leeg   {{ color: #a0b4c2; font-style: italic; padding: 20px 0; }}
"""


class HtmlPreviewBuilder:
    """Zet een ReportPackage om naar een HTML-string voor QTextBrowser."""

    def build(self, package: ReportPackage) -> str:
        """Genereer HTML-string voor de geselecteerde secties.

        Parameters
        ----------
        package:
            Rapportpakket met invoer- en resultaatsecties en de selectielijst.

        Returns
        -------
        str
            Volledige HTML-string geschikt voor QTextBrowser.setHtml().
        """
        titel = package.metadata.project_name or 'Rapport'

        secties: list[str] = []
        for item in package.selected_items:
            if item.kind == 'invoer':
                sec = next(
                    (s for s in package.input_sections if s.id == item.source_ref),
                    None,
                )
            elif item.kind == 'resultaat':
                sec = next(
                    (s for s in package.result_sections if s.id == item.source_ref),
                    None,
                )
            else:
                sec = None
            if sec is not None:
                secties.append(self._sectie_html(sec))

        body = '\n'.join(secties) if secties else '<p class="leeg">Geen secties geselecteerd.</p>'

        return (
            f'<!DOCTYPE html><html><head>'
            f'<meta charset="utf-8">'
            f'<style>{_CSS}</style>'
            f'</head><body>'
            f'<h1>{_esc(titel)}</h1>'
            f'{body}'
            f'</body></html>'
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sectie_html(self, sec: ReportSection) -> str:
        """Render één ReportSection als HTML-fragment."""
        delen: list[str] = [f'<h2>{_esc(sec.title)}</h2>']

        if sec.fields:
            delen.append(self._velden_html(sec.fields))

        for tabel in sec.tables:
            delen.append(self._tabel_html(tabel))

        for blok in sec.text_blocks:
            tekst = blok.effective_text
            if tekst:
                delen.append(f'<p class="tekst">{_esc(tekst)}</p>')

        return '\n'.join(delen)

    def _velden_html(self, velden: list[ReportField]) -> str:
        """Render veld-rijen als HTML-tabel."""
        rijen = []
        for i, veld in enumerate(velden):
            klasse = 'odd' if i % 2 == 0 else 'even'
            unit_cel = f'<td class="unit">{_esc(veld.unit)}</td>' if veld.unit else '<td></td>'
            rijen.append(
                f'<tr class="{klasse}">'
                f'<td class="label">{_esc(veld.label)}</td>'
                f'<td class="value">{_esc(veld.value)}</td>'
                f'{unit_cel}'
                f'</tr>'
            )
        return f'<table>{"".join(rijen)}</table>'

    def _tabel_html(self, tabel: ReportTable) -> str:
        """Render een ReportTable als HTML-tabel met header."""
        header = ''.join(f'<th>{_esc(k)}</th>' for k in tabel.columns)
        rijen = []
        for i, rij in enumerate(tabel.rows):
            klasse = 'odd' if i % 2 == 0 else 'even'
            cellen = ''.join(f'<td>{_esc(cel)}</td>' for cel in rij)
            rijen.append(f'<tr class="{klasse}">{cellen}</tr>')
        if tabel.title:
            kop = f'<p style="font-size:11px;font-weight:600;color:{_LABEL};margin:8px 0 3px;">{_esc(tabel.title)}</p>'
        else:
            kop = ''
        return f'{kop}<table><tr>{header}</tr>{"".join(rijen)}</table>'


def _esc(tekst: str) -> str:
    """Vervang HTML-speciale tekens door entiteiten."""
    return (
        tekst
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )
```

- [ ] **Stap 4: Voer tests uit — verwacht PASS**

```bash
pytest tests/test_html_preview_builder.py -v
```

Verwacht: 8 × PASSED

- [ ] **Stap 5: Alle tests nog steeds groen**

```bash
pytest tests/ -v
```

Verwacht: alle tests PASSED

- [ ] **Stap 6: Commit**

```bash
git add reporting/builders/html_preview_builder.py tests/test_html_preview_builder.py
git commit -m "feat: voeg HtmlPreviewBuilder toe voor Word-preview"
```

---

## Task 3: WordPreviewWindow

**Files:**
- Create: `ui/preview_window.py`

Geen unit-tests voor PyQt6-UI-klassen. Handmatig testen in Task 5.

- [ ] **Stap 1: Maak `ui/preview_window.py` aan**

```python
"""Zwevend Word-preview venster voor D-Sheet Dashboard."""

from __future__ import annotations
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
)
from PyQt6.QtCore import QSettings


class WordPreviewWindow(QMainWindow):
    """Zwevend venster dat een HTML-rapportweergave toont in QTextBrowser.

    Het venster is bewust 'dom': het ontvangt alleen een HTML-string via
    set_html() en heeft geen directe toegang tot AppState of controllers.
    Positie en grootte worden onthouden via QSettings.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Word Preview')
        self.resize(720, 900)
        self._build()
        self._herstel_geometrie()

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Statusbalk ────────────────────────────────────────────────
        status_balk = QWidget()
        status_balk.setStyleSheet(
            'background: #f0f4f7; border-bottom: 1px solid #c4d4e0;'
        )
        status_layout = QHBoxLayout(status_balk)
        status_layout.setContentsMargins(10, 4, 10, 4)
        status_layout.setSpacing(0)

        self._count_label = QLabel('Geen secties')
        self._count_label.setStyleSheet(
            'font-size: 10px; color: #5a7a8a; '
            'font-family: "Segoe UI", sans-serif;'
        )
        self._tijd_label = QLabel('')
        self._tijd_label.setStyleSheet(
            'font-size: 10px; color: #999; font-style: italic; '
            'font-family: "Segoe UI", sans-serif;'
        )

        status_layout.addWidget(self._count_label)
        status_layout.addStretch()
        status_layout.addWidget(self._tijd_label)
        layout.addWidget(status_balk)

        # ── Preview-browser ───────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.setStyleSheet('border: none; background: white;')
        layout.addWidget(self._browser, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_html(self, html: str, sectie_count: int = 0) -> None:
        """Toon nieuwe HTML-inhoud en werk de statusbalk bij.

        Parameters
        ----------
        html:
            Volledige HTML-string voor QTextBrowser.setHtml().
        sectie_count:
            Aantal geselecteerde secties voor de statusregel.
        """
        self._browser.setHtml(html)
        enkelvoud = sectie_count == 1
        self._count_label.setText(
            f'{sectie_count} sectie geselecteerd'
            if enkelvoud else
            f'{sectie_count} secties geselecteerd'
        )
        self._tijd_label.setText(
            f'↻ Bijgewerkt: {datetime.now().strftime("%H:%M")}'
        )

    # ------------------------------------------------------------------
    # Geometrie-persistentie
    # ------------------------------------------------------------------

    def _herstel_geometrie(self) -> None:
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        geom = instellingen.value('preview_window/geometry')
        if geom:
            self.restoreGeometry(geom)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        instellingen.setValue('preview_window/geometry', self.saveGeometry())
        super().closeEvent(event)
```

- [ ] **Stap 2: Commit**

```bash
git add ui/preview_window.py
git commit -m "feat: voeg WordPreviewWindow toe als zwevend QMainWindow"
```

---

## Task 4: TabInstellingen

**Files:**
- Create: `ui/tabs/tab_instellingen.py`

- [ ] **Stap 1: Maak `ui/tabs/tab_instellingen.py` aan**

```python
"""Tab Instellingen — persistente app-instellingen en preview-opener."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog,
)
from PyQt6.QtCore import pyqtSignal

_BTN_PRIMARY = (
    'QPushButton { background: #245b7a; color: white; border: 1px solid #1a4560; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; } '
    'QPushButton:hover { background: #1a4560; } '
    'QPushButton:pressed { background: #122f42; }'
)
_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 4px 10px; font-size: 11px; } '
    'QPushButton:hover { background: #f0f5f9; } '
    'QPushButton:pressed { background: #e4edf3; }'
)
_BTN_CLEAR = (
    'QPushButton { background: white; color: #888; border: 1px solid #ccc; '
    'border-radius: 5px; padding: 4px 6px; font-size: 11px; } '
    'QPushButton:hover { background: #fdf0ee; color: #c0392b; border-color: #c0392b; }'
)


class TabInstellingen(QWidget):
    """Tabblad met persistente applicatie-instellingen (Tab Instellingen)."""

    template_path_changed = pyqtSignal(str)
    """Afgegeven zodra het Word-template-pad wijzigt (ook bij wissen)."""

    preview_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Preview openen' klikt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Groep: Rapportage-instellingen ────────────────────────────
        tmpl_box = QGroupBox('Rapportage-instellingen')
        tmpl_vl = QVBoxLayout(tmpl_box)
        tmpl_vl.setSpacing(6)

        lbl = QLabel('Word-template (.docx)')
        lbl.setStyleSheet('font-size: 11px; color: #444;')

        tmpl_rij = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .docx template… (optioneel)')
        self._template_edit.textChanged.connect(self.template_path_changed)

        bladeren_btn = QPushButton('Bladeren…')
        bladeren_btn.setStyleSheet(_BTN_NORMAL)
        bladeren_btn.clicked.connect(self._on_bladeren)

        wis_btn = QPushButton('✕')
        wis_btn.setStyleSheet(_BTN_CLEAR)
        wis_btn.setFixedWidth(28)
        wis_btn.setToolTip('Verwijder template-pad')
        wis_btn.clicked.connect(self._on_wis_template)

        tmpl_rij.addWidget(self._template_edit)
        tmpl_rij.addWidget(bladeren_btn)
        tmpl_rij.addWidget(wis_btn)

        hint = QLabel(
            'Optioneel — wordt ook gebruikt bij Word-export als het export-venster leeg is'
        )
        hint.setStyleSheet('font-size: 10px; color: #888; font-style: italic;')

        tmpl_vl.addWidget(lbl)
        tmpl_vl.addLayout(tmpl_rij)
        tmpl_vl.addWidget(hint)
        root.addWidget(tmpl_box)

        # ── Groep: Preview-venster ────────────────────────────────────
        prev_box = QGroupBox('Preview-venster')
        prev_vl = QVBoxLayout(prev_box)
        prev_vl.setSpacing(6)

        prev_rij = QHBoxLayout()
        open_btn = QPushButton('↗ Preview openen')
        open_btn.setStyleSheet(_BTN_PRIMARY)
        open_btn.clicked.connect(self.preview_open_requested)

        prev_hint = QLabel('Opent een zwevend Word-preview venster naast de applicatie')
        prev_hint.setStyleSheet('font-size: 10px; color: #666;')

        prev_rij.addWidget(open_btn)
        prev_rij.addWidget(prev_hint)
        prev_rij.addStretch()
        prev_vl.addLayout(prev_rij)
        root.addWidget(prev_box)

        root.addStretch()

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_template_path(self, pad: str) -> None:
        """Toon een opgeslagen template-pad zonder een signal af te geven.

        Parameters
        ----------
        pad:
            Te tonen bestandspad (leeg = veld wissen).
        """
        self._template_edit.blockSignals(True)
        self._template_edit.setText(pad)
        self._template_edit.blockSignals(False)

    # ------------------------------------------------------------------
    # Privé handlers
    # ------------------------------------------------------------------

    def _on_bladeren(self) -> None:
        pad, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer Word-template', '', 'Word (*.docx)'
        )
        if pad:
            self._template_edit.setText(pad)

    def _on_wis_template(self) -> None:
        self._template_edit.clear()
```

- [ ] **Stap 2: Commit**

```bash
git add ui/tabs/tab_instellingen.py
git commit -m "feat: voeg TabInstellingen toe met template-pad en preview-knop"
```

---

## Task 5: MainWindow-integratie + ReportController-fallback

**Files:**
- Modify: `app/main_window.py`
- Modify: `app/report_controller.py`

- [ ] **Stap 1: Imports toevoegen aan `app/main_window.py`**

Voeg toe aan de import-blokken (lokale imports onderaan, vóór de bestaande `from ui.tabs...` regels):

```python
from app.settings import AppSettings
from ui.tabs.tab_instellingen import TabInstellingen
from ui.preview_window import WordPreviewWindow
from reporting.builders.html_preview_builder import HtmlPreviewBuilder
```

- [ ] **Stap 2: Instellingen-tab toevoegen in `_build_ui()`**

Voeg toe na de Validatie-tab (na `self._main_tabs.addTab(self._tab_validation, 'Validatie')`):

```python
        # Tab Instellingen
        self._tab_instellingen = TabInstellingen()
        self._main_tabs.addTab(self._tab_instellingen, 'Instellingen')
```

- [ ] **Stap 3: Preview-venster en builder aanmaken in `__init__()`**

Voeg toe na `self._controller.load_config()` (regel ~109):

```python
        self._preview_window = WordPreviewWindow()
        self._html_builder = HtmlPreviewBuilder()
```

- [ ] **Stap 4: Beginwaarden instellen na `_connect_signals()`**

Voeg toe na de aanroep van `_connect_signals()` in `__init__()`:

```python
        self._tab_instellingen.set_template_path(
            self._state.app_settings.word_template_path
        )
```

- [ ] **Stap 5: Signalen koppelen in `_connect_signals()`**

Voeg toe onderaan `_connect_signals()`, voor de sluitende regel:

```python
        self._tab_instellingen.template_path_changed.connect(
            self._on_template_path_changed
        )
        self._tab_instellingen.preview_open_requested.connect(
            self._on_preview_open
        )
```

- [ ] **Stap 6: Event handlers toevoegen**

Voeg de drie handlers toe bij de rapportage event handlers (na `_on_validate`):

```python
    def _on_template_path_changed(self, pad: str) -> None:
        """Sla gewijzigd template-pad op in state en config."""
        self._controller.apply_app_settings(AppSettings(word_template_path=pad))

    def _on_preview_open(self) -> None:
        """Open het preview-venster en render direct."""
        self._preview_window.show()
        self._preview_window.raise_()
        self._update_preview()

    def _update_preview(self) -> None:
        """Herrender de HTML-preview als het venster zichtbaar is."""
        if not self._preview_window.isVisible():
            return
        package = self._report_controller.build_package()
        html = self._html_builder.build(package)
        self._preview_window.set_html(html, len(package.selected_items))
```

- [ ] **Stap 7: `_update_all()` uitbreiden**

Zoek de methode `_update_all()` (regel ~600) en voeg `self._update_preview()` toe:

```python
    def _update_all(self) -> None:
        self._update_render_views()
        self._refresh_active_report_tab()
        self._update_preview()
```

- [ ] **Stap 8: Fallback template-pad in `app/report_controller.py`**

Vervang de bestaande `export_word()` methode:

```python
    def export_word(self, output_path: str) -> str | None:
        """Exporteer naar Word.

        Gebruikt als template (in volgorde van prioriteit):
        1. Het pad ingevuld in TabWordExport (ReportState.template_word)
        2. Het persistente pad uit AppSettings (AppState.app_settings.word_template_path)
        3. Geen template (leeg document)

        Returns
        -------
        None bij succes, foutmelding (str) bij een fout.
        """
        package = self.build_package()
        template = (
            self._report.template_word
            or self._app.app_settings.word_template_path
            or None
        )
        return self._word.export(package, template, output_path)
```

- [ ] **Stap 9: Handmatig testen**

Start de applicatie:

```bash
python run.pyw
```

Controleer:
1. Tabblad "Instellingen" verschijnt als laatste tab
2. Klik "↗ Preview openen" → een zwevend venster opent
3. Preview toont "Geen secties geselecteerd" als er geen project geladen is
4. Laad een `.shi`-bestand en verwerk → preview toont secties automatisch na laden
5. Template-pad invullen in Instellingen-tab → veld is gevuld na herstart van de app
6. Sluiten van preview-venster → heropen via knop → venster opent op zelfde positie
7. Word-export zonder template in het export-tabje maar mét pad in Instellingen → gebruikt het instellingen-pad

- [ ] **Stap 10: Alle tests groen**

```bash
pytest tests/ -v
```

Verwacht: alle tests PASSED

- [ ] **Stap 11: Commit**

```bash
git add app/main_window.py app/report_controller.py
git commit -m "feat: koppel WordPreviewWindow en TabInstellingen aan MainWindow"
```

---

## Afrondende controle

Na alle taken:

```bash
pytest tests/ -v
python run.pyw
```

Controleer:
- Geen regressies in bestaande functionaliteit (import, parsing, rendering, exports)
- Preview werkt automatisch bij wisselen van project of rapportselectie
- Template-pad wordt correct opgeslagen/geladen
