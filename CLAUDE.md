# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**D-Sheet Dashboard** is a PyQt6 desktop application for visualizing D-Sheet damwand (sheet pile wall) geotechnical calculations from `.shi`/`.shd`/`.shs` file formats. Documentation and UI labels are in Dutch.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt           # runtime
pip install -r requirements-dev.txt       # incl. pytest voor tests

# Run the application
python run.pyw

# Run tests
pytest tests/test_parsers.py -v
```

No linting configuration is present in the project.

## Architecture

The application follows a **data → parse → visualize → interact** pipeline with centralized state.

### Data Flow

1. User drags/imports `.shi`/`.shd`/`.shs` files → `AppController.ingest_paths()` → stored as raw text in `AppState.raw_files`
2. User clicks "Verwerk" (Process) → `AppController.process_files()` → files grouped by base name into `FileBundle` → `parse_project()` → `AppState.projects`
3. `_update_all()` → `_update_render_views()` (viewport + drawing) + `_refresh_active_report_tab()` (on-demand report tab refresh)
4. `SectionRenderer.render()` draws the cross-section; `render_output_charts()` draws moment/shear/displacement graphs
5. Any UI interaction (combo box, zoom, settings) → signal → handler calls `AppController` method → updates `AppState` → `_update_all()` → re-render

### Module Map

| Package | Purpose |
|---|---|
| `app/` | App layer: state, controller, config, viewport, main window, report controller |
| `parsers/` | `.shi`/`.shd`/`.shs` parsing → domain dataclasses (`Project`, `Stage`, `SoilLayer`, etc.) |
| `renderers/` | Matplotlib renderers: cross-section (`SectionRenderer`) and results charts (`render_output_charts`) |
| `ui/` | PyQt6 widgets and 11 tab modules under `ui/tabs/` |
| `reporting/` | Report models, `ReportPlan`, validation, and description builders |
| `exporters/` | `ExcelExporter` (openpyxl) and `WordExporter` (python-docx) |
| `utils/` | Color conversion, geometry helpers, Dutch number formatting, PNG/PDF export |

### Design Rules

- **Centralized state**: All state mutations go through `AppController` or `ReportController`; the view never writes to `AppState` directly
- **No Qt in controllers**: `AppController`, `ReportController`, `ConfigManager`, `ViewportService` have zero Qt imports
- **No widget aliases**: In `main_window.py` all tab widgets are accessed directly via `self._tab_<name>.<widget>` — do not introduce aliases
- **BaseRenderer ABC**: New renderers must subclass `renderers.BaseRenderer` and implement `render(ax, project, stage, settings, viewport)`
- **Parser registry**: New file format support = call `register_parser(ext, fn)` in `parsers/__init__.py`
- **Text overrides**: `ReportState.overrides` maps `block_id → override_text`; `TextBlock.effective_text` returns override if set, else generated text
- **Render settings always passed**: `AppController.render_results()` always passes `self._state.render_settings` to `render_output_charts()`
- **ViewportService dependencies**: `y_range_for_project()`, `x_range_for_project()`, `get_stage_profile()` are module-level exports from `section_renderer.py` used by `ViewportService`

---

## Coding Conventions

### Python Style

#### Naamgeving
- **Variabelen & functies**: `snake_case` — ook domeinvariabelen in het Nederlands: `grondlagen`, `maaiveld`, `waterstand`, `bouwfase`
- **Klassen**: `PascalCase` — `AppState`, `SectionRenderer`, `MainWindow`
- **Bestanden/modules**: `snake_case` — `config_manager.py`, `shi_parser.py`
- **Private attributen en methoden**: voorloopstreep `_` — `_state`, `_controller`, `_on_import`, `_normalize_name`
- **Constanten**: `ALL_CAPS_WITH_UNDERSCORES` op moduleniveau — `CONFIG_DIR`, `_CARD_STYLE`, `_BTN_PRIMARY`
- **Taal**: Nederlands is leidend — variabelenamen, commentaar, docstrings en UI-teksten zijn in het Nederlands; Engels alleen voor library-imports en typeannotaties

#### Type hints
- Elke functieparameter en returntype expliciet annoteren
- Gebruik `str | None` (Python 3.10+ syntax), **niet** `Optional[str]`
- Zet `from __future__ import annotations` bovenaan elk bestand (vóór stdlib-imports)

#### Docstrings
- NumPy/Google-stijl met `Parameters\n----------` en `Returns\n-------` secties
- Beschrijvingen in het Nederlands
- Aanwezig op alle klassen en publieke methoden

#### Imports
Volgorde (gescheiden door lege regels):
1. `from __future__ import annotations`
2. Standaardbibliotheek (`import json`, `from pathlib import Path`)
3. Third-party (`PyQt6`, `matplotlib`, `numpy`)
4. Lokale imports (`app`, `parsers`, `renderers`, `ui`, `utils`, `reporting`, `exporters`)

#### Formattering
- F-strings altijd, nooit `.format()` of `%`-formattering
- Nederlandse getalnotatie via `fmt_number()` uit `utils/formatting.py` (komma als decimaalteken)

---

### Foutafhandeling

- **Returntuples voor herstelbare fouten**: `tuple[bool, str]` — `(succes, bericht)` — in plaats van exceptions gooien
- **UI toont fouten via `QMessageBox.warning()`** op basis van het teruggegeven bericht
- Brede `except Exception as exc` catch; converteer naar leesbare string voor de gebruiker
- Alle afhankelijkheden worden bij app-start gecontroleerd in `run.pyw`; imports zijn altijd op moduleniveau — **geen** lazy `try/except ImportError` in exporters of andere modules

---

### Klassen & datastructuren

#### Dataclasses
- **Domeinmodellen zijn `@dataclass`** — `Project`, `Stage`, `SoilLayer`, `Anchor`, etc.
- Gebruik `field(default_factory=list)` voor muteerbare standaardwaarden
- Instellingsobjecten zijn ook dataclasses: `RenderSettings`, `ViewportSettings`; nooit ruwe dicts doorgeven

#### Service/controller-klassen
- Geen Qt-imports in controllers en services
- Afhankelijkheden als instantievariabelen in `__init__` — geen globale state, geen singletons
- Methoden gegroepeerd per verantwoordelijkheid, gescheiden door commentaarblokken:
  ```python
  # ------------------------------------------------------------------
  # Bestandsingest
  # ------------------------------------------------------------------
  ```

#### `__init__.py`
- Minimaal: alleen een korte opmerking als pakketmarkering; geen re-exports

---

### PyQt6-patronen

#### Widgets
- Alle widgets opgeslagen als `self._<naam>` (private instantievariabelen)
- Widgetopbouw altijd in een aparte `_build(self) -> None`-methode, aangeroepen aan het einde van `__init__`
- Constructorsignatuur: `def __init__(self, parent: QWidget | None = None) -> None:`
- Layouts altijd expliciet `setContentsMargins()` en `setSpacing()` meegeven (typische waarden: margins 4–12 px, spacing 4–8 px)

#### Signalen & slots
- Signalen gedefinieerd als klasseattribuut: `project_selected = pyqtSignal(str)`
- Alle verbindingen gecentraliseerd in `_connect_signals()` in `main_window.py`
- Event-handlers heten `_on_<gebeurtenis>()` met voorloopstreep
- Programmatische UI-updates zonder signaalcascade via `blockSignals(True/False)`:
  ```python
  widget.blockSignals(True)
  widget.setValue(val)
  widget.blockSignals(False)
  ```

#### Tabs
- Elke tab is een onafhankelijke `QWidget`-subklasse in `ui/tabs/tab_<naam>.py`
- Tab-inhoud wordt on-demand vernieuwd in `_on_main_tab_changed()`

---

### Matplotlib-patronen

- Stel de backend in met `matplotlib.use('QtAgg')` vóór canvasimports, op moduleniveau
- Gebruik `FigureCanvasQTAgg` voor Qt-geïntegreerde figuren; `FigureCanvasAgg` voor headless/export
- Teken-cyclus: `ax.cla()` → render → `fig.tight_layout()` → `canvas.draw()`
- Alle tekenfuncties in `renderers/draw_helpers.py` accepteren `ax: Axes` als eerste parameter
- Nieuwe renderers: subklasse `renderers.BaseRenderer`, implementeer `render(ax, project, stage, settings, viewport)`

---

### Terugkerende patronen

#### UI → state → render
```python
# 1. Lees UI-waarden
settings = self._read_viewport()
# 2. Schrijf naar state via controller
self._controller.apply_viewport_settings(settings)
# 3. Herrender
self._render_section()
```

#### `_find()`-helper
Gedefinieerd lokaal in modules die een lijst op naam doorzoeken:
```python
def _find(lst, name: str):
    return next((x for x in (lst or []) if x.name == name), None)
```
Niet importeren vanuit een gedeelde locatie — elke module definieert zijn eigen kopie.

#### Rapportage-pipeline
Builder → `ReportSection` → Exporter (Excel/Word)
