# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**D-Sheet Dashboard** is a PyQt6 desktop application for visualizing D-Sheet damwand (sheet pile wall) geotechnical calculations from `.shi`/`.shd`/`.shs` file formats. Documentation and UI labels are in Dutch.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt           # runtime
pip install -r DEV/requirements-dev.txt   # incl. pytest voor tests

# Run the application
python run.pyw

# Run tests
pytest DEV/tests/test_parsers.py -v
```

No linting configuration is present in the project.

## Architecture

The application follows a **data â†’ parse â†’ visualize â†’ interact** pipeline with centralized state.

### Data Flow

1. User drags/imports `.shi`/`.shd`/`.shs` files â†’ `AppController.ingest_paths()` â†’ stored as raw text in `AppState.raw_files`
2. User clicks "Verwerk" (Process) â†’ `AppController.process_files()` â†’ files grouped by base name into `FileBundle` â†’ `parse_project()` â†’ `AppState.projects`
3. `_update_all()` â†’ `_update_render_views()` (viewport + drawing) + `_refresh_active_report_tab()` (on-demand report tab refresh)
4. `SectionRenderer.render()` draws the cross-section; `render_output_charts()` draws moment/shear/displacement graphs
5. Any UI interaction (combo box, zoom, settings) â†’ signal â†’ handler calls `AppController` method â†’ updates `AppState` â†’ `_update_all()` â†’ re-render

### Module Map

| Package | Purpose |
|---|---|
| `app/` | App layer: state, controller, config, viewport, main window, report controller, theme + theme_apply |
| `parsers/` | `.shi`/`.shd`/`.shs` parsing â†’ domain dataclasses (`Project`, `Stage`, `SoilLayer`, etc.) |
| `renderers/` | Matplotlib renderers: cross-section, results charts, vertical equilibrium |
| `ui/` | PyQt6 widgets, theme dialog, table styles, and 14 tab modules under `ui/tabs/` |
| `reporting/` | Report models, `ReportPlan`, and builders (input/result description, soil table, damwand chapter) |
| `exporters/` | `WordHoofdstukExporter` |
| `utils/` | Color conversion, geometry helpers, Dutch number formatting, PNG/PDF export |
| `themes/` | JSON-defined themes (DKIB, SIX Geoconsult) loaded by `app/theme.py` |
| `templates/` | Word templates for export (`damwand_stijlen.docx`) |
| `DEV/` | Development-only material: tests, dev requirements, dead-code archive, local docs, and cache folders |

### Repository Layout Rule

Runtime app construction stays in the root runtime packages: `app/`, `ui/`,
`parsers/`, `renderers/`, `reporting/`, `exporters/`, `utils/`, `themes/`, and
`templates/`, plus `run.pyw`, `requirements.txt`, and helper scripts.

Everything that is not needed to build or run the app belongs under `DEV/`:
`DEV/tests/`, `DEV/requirements-dev.txt`, `DEV/DEAD/`, `DEV/docs/`, and
`DEV/cache/`. Do not import runtime code from `DEV/`; it is for verification,
analysis, archives, and local generated artifacts only.

### Design Rules

- **Centralized state**: All state mutations go through `AppController` or `ReportController`; the view never writes to `AppState` directly
- **No Qt in controllers**: `AppController`, `ReportController`, `ConfigManager`, `ViewportService` have zero Qt imports
- **No widget aliases**: In `main_window.py` all tab widgets are accessed directly via `self._tab_<name>.<widget>` â€” do not introduce aliases
- **BaseRenderer ABC**: New renderers must subclass `renderers.BaseRenderer` and implement `render(ax, project, stage, settings, viewport)`
- **Parsing**: D-Sheet `.shi/.shd/.shs` bundles are parsed directly via `parsers.shi_parser.parse_project`.
- **Text overrides**: `ReportState.overrides` maps `block_id â†’ override_text`; `TextBlock.effective_text` returns override if set, else generated text
- **Render settings always passed**: `AppController.render_results()` always passes `self._state.render_settings` to `render_output_charts()`
- **ViewportService dependencies**: `y_range_for_project()`, `x_range_for_project()`, `get_stage_profile()` are module-level exports from `section_renderer.py` used by `ViewportService`
- **Theme system**: themes are JSON files in `themes/`, loaded via `app.theme.discover_themes()`; `bootstrap_theme()` applies the active theme to the `QApplication` at startup; widgets pull QSS-driven styling â€” avoid inline stylesheets in `main_window.py`

---

## Coding Conventions

### Python Style

#### Naamgeving
- **Variabelen & functies**: `snake_case` â€” ook domeinvariabelen in het Nederlands: `grondlagen`, `maaiveld`, `waterstand`, `bouwfase`
- **Klassen**: `PascalCase` â€” `AppState`, `SectionRenderer`, `MainWindow`
- **Bestanden/modules**: `snake_case` â€” `config_manager.py`, `shi_parser.py`
- **Private attributen en methoden**: voorloopstreep `_` â€” `_state`, `_controller`, `_on_import`, `_normalize_name`
- **Constanten**: `ALL_CAPS_WITH_UNDERSCORES` op moduleniveau â€” `CONFIG_DIR`, `THEMES_DIR`, `BASIC_THEME_NAME`
- **Taal**: Nederlands is leidend â€” variabelenamen, commentaar, docstrings en UI-teksten zijn in het Nederlands; Engels alleen voor library-imports en typeannotaties

#### Type hints
- Elke functieparameter en returntype expliciet annoteren
- Gebruik `str | None` (Python 3.10+ syntax), **niet** `Optional[str]`
- Zet `from __future__ import annotations` bovenaan elk bestand (vÃ³Ã³r stdlib-imports)

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

- **Returntuples voor herstelbare fouten**: `tuple[bool, str]` â€” `(succes, bericht)` â€” in plaats van exceptions gooien
- **UI toont fouten via `QMessageBox.warning()`** op basis van het teruggegeven bericht
- Brede `except Exception as exc` catch; converteer naar leesbare string voor de gebruiker
- Alle afhankelijkheden worden bij app-start gecontroleerd in `run.pyw`; imports zijn altijd op moduleniveau â€” **geen** lazy `try/except ImportError` in exporters of andere modules

---

### Klassen & datastructuren

#### Dataclasses
- **Domeinmodellen zijn `@dataclass`** â€” `Project`, `Stage`, `SoilLayer`, `Anchor`, etc.
- Gebruik `field(default_factory=list)` voor muteerbare standaardwaarden
- Instellingsobjecten zijn ook dataclasses: `RenderSettings`, `ViewportSettings`; nooit ruwe dicts doorgeven

#### Service/controller-klassen
- Geen Qt-imports in controllers en services
- Afhankelijkheden als instantievariabelen in `__init__` â€” geen globale state, geen singletons
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
- Layouts altijd expliciet `setContentsMargins()` en `setSpacing()` meegeven (typische waarden: margins 4â€“12 px, spacing 4â€“8 px)

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

- Stel de backend in met `matplotlib.use('QtAgg')` vÃ³Ã³r canvasimports, op moduleniveau
- Gebruik `FigureCanvasQTAgg` voor Qt-geÃ¯ntegreerde figuren; `FigureCanvasAgg` voor headless/export
- Teken-cyclus: `ax.cla()` â†’ render â†’ `fig.tight_layout()` â†’ `canvas.draw()`
- Alle tekenfuncties in `renderers/draw_helpers.py` accepteren `ax: Axes` als eerste parameter
- Nieuwe renderers: subklasse `renderers.BaseRenderer`, implementeer `render(ax, project, stage, settings, viewport)`

---

### Terugkerende patronen

#### UI â†’ state â†’ render
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
Niet importeren vanuit een gedeelde locatie â€” elke module definieert zijn eigen kopie.

#### Rapportage-pipeline
Builder -> `ReportSection` -> `WordHoofdstukExporter`

