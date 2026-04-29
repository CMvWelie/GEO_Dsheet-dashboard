# App-laag

Applicatielaag van D-Sheet Dashboard. Bevat de centrale state, controllers, configuratiepersistentie, viewport-logica en het thema-systeem. Met uitzondering van `main_window.py` en `theme_apply.py` zijn alle modules vrij van Qt-imports zodat ze los van de UI testbaar blijven.

## Bestanden

| Bestand | Doel |
|---|---|
| `__init__.py` | Pakketmarkering, geen re-exports. |
| `state.py` | `AppState` dataclass: projecten, actieve selecties, raw files en settings; single source of truth. |
| `settings.py` | Dataclasses `RenderSettings`, `ViewportSettings` en `AppSettings` voor render-, viewport- en app-instellingen. |
| `controller.py` | `AppController` orkestreert ingest, parsing, rendering, viewport en export; retourneert `(succes, bericht)`-tuples. |
| `report_controller.py` | `ReportController` orkestreert builders, plan en exporters voor de rapportagepijplijn. |
| `report_state.py` | `ReportState` dataclass: metadata, plan, templatepaden en TextBlock-overrides. |
| `config_manager.py` | `ConfigManager` leest en schrijft `~/.dsheet_dashboard/config.json` (render/viewport/app-secties). |
| `viewport_service.py` | `ViewportService` berekent auto-grenzen en zoom-transformaties op basis van projectdata. |
| `theme.py` | Thema-dataclasses (`Theme`, `ThemeColors`, `ThemeTypography`, `ThemeGeometry`, `ThemeAssets`, `ThemeTableStyle`); JSON-loader en QSS-builder, geen Qt. |
| `theme_apply.py` | `bootstrap_theme()` registreert fonts en past stylesheet toe op de actieve `QApplication`; enige Qt-aware module hier naast `main_window.py`. |
| `main_window.py` | `QMainWindow` met topbalk en tabwidget; verbindt UI-signals met controller-methoden in `_connect_signals()`. |

## Conventies

- **Geen Qt-imports** in `state.py`, `settings.py`, `controller.py`, `report_controller.py`, `report_state.py`, `config_manager.py`, `viewport_service.py` en `theme.py`. Qt is alleen toegestaan in `main_window.py` en `theme_apply.py`.
- **State-mutaties uitsluitend via controllers**: de view leest uit `AppState`/`ReportState` maar schrijft nooit rechtstreeks.
- **Foutafhandeling via returntuples** `(bool, str)` of foutmeldingen als `str | None`; geen exceptions voor herstelbare gebruikersfouten.
- **Dataclasses voor configuratie en state**, nooit ruwe dicts doorgeven. Muteerbare velden via `field(default_factory=...)`.
- **Type hints overal**, met `str | None` (Python 3.10+ syntax) en `from __future__ import annotations` bovenaan elk bestand.
- **`__init__.py` minimaal**: alleen pakketmarkering, geen re-exports.
- Methoden gegroepeerd per verantwoordelijkheid met commentaarbanners (`# Config`, `# Bestandsingest`, `# Rendering`, etc.).

## Datastroom

`run.pyw` roept `bootstrap_theme()` aan en construeert `MainWindow`, dat één `AppState` en één `ReportState` instantieert plus de bijbehorende `AppController` en `ReportController`. UI-signals uit de tabs gaan via `_connect_signals()` naar de controllers; die muteren state, vragen `ConfigManager` om persistentie en `ViewportService` om auto-bounds, en sturen vervolgens de renderers en exporters in de andere lagen aan.
