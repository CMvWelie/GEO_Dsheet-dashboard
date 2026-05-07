# Dode-code-analyse — D-Sheet Dashboard

Gegenereerd: 2026-05-07

---

## HIGH — Volledige modules die nergens worden geïmporteerd

| Pad | Symbool | Reden |
|---|---|---|
| `ui/sidebar.py` | `Sidebar` (r.42), `StatusLabel` (r.13) | Nergens geïmporteerd. Vervangen door `TabReportContext` en `StatusWidget`. |
| `ui/file_list_widget.py` | `FileListWidget` (r.8) | Alleen geïmporteerd door dode `sidebar.py`. |
| `ui/controls_panel.py` | `ControlsPanel` (r.13) | Nergens gebruikt. Vervangen door knoppen in `tab_input_view.py`. |
| `ui/layer_table.py` | `LayerTableWidget` (r.15) | Nergens geïmporteerd. Functionaliteit zit in `info_panel.py`. |
| `ui/preview_window.py` | `WordPreviewWindow` (r.12) | Vervangen door `WordPdfPreviewWindow` uit `word_pdf_preview_window.py`. |
| `exporters/word_exporter.py` | `WordExporter` (r.40) | Alleen in tests. Productie gebruikt `WordHoofdstukExporter`. |
| `exporters/excel_exporter.py` | `ExcelExporter` (r.25) | Alleen aangeroepen door dode `ReportController.export_excel`. |
| `reporting/builders/html_preview_builder.py` | `HtmlPreviewBuilder` (r.58) | Alleen in tests. Productie gebruikt Word→PDF pipeline. |

---

## HIGH — Dode publieke methoden

| Pad | Symbool | Reden |
|---|---|---|
| `app/report_controller.py:50` | `build_input_descriptions` | Nergens aangeroepen. |
| `app/report_controller.py:100` | `set_template_excel` | Nergens aangeroepen. |
| `app/report_controller.py:123` | `get_plan` | Nergens aangeroepen. |
| `app/report_controller.py:202` | `export_excel` | Nergens aangeroepen; bevat enige call van `ExcelExporter`. |
| `app/report_controller.py:173` | `build_package` | Alleen door dode `export_excel` en tests. |
| `app/report_controller.py:58` | `build_damwand_sections` | Alleen door dode `build_package`. |
| `app/report_controller.py:83` | `build_soil_sections` | Alleen door dode `build_package`. |
| `app/report_controller.py:186` | `build_metadata` | **BUG**: leest `rs.project_name`, `rs.client`, `rs.author` etc. die niet bestaan op `ReportState`. Geeft altijd lege `ReportMetadata`. Echte metadata zit in `rs.metadata`. |
| `app/controller.py:181` | `apply_zoom` | Nergens aangeroepen. |
| `app/controller.py:187` | `reset_viewport` | Nergens aangeroepen. |
| `app/controller.py:327` | `sort_result_steps` | Nergens aangeroepen — `MainWindow._result_step_sort` gebruikt direct de statische helper. |
| `parsers/__init__.py:21` | `get_parser` | Niet aangeroepen — `AppController.process_files` bypast registry en roept `parse_project` rechtstreeks aan. |
| `reporting/builders/damwand_hoofdstuk_builder.py:28` | `build_input_sections` | Alleen via dode `build_damwand_sections`. |
| `reporting/builders/input_description_builder.py:258` | `build` + helpers `_tb`, `_sheet_piling`, `_geometry`, `_water`, `_loads`, `_anchors`, `_struts`, `_supports`, `_soil_layers` (r.272–443) | Alleen via dode `ReportController.build_input_descriptions`. |
| `renderers/draw_helpers.py:49` | `fill_with_vertical_hatch` | Geen call sites. |
| `renderers/draw_helpers.py:81` | `fill_with_surface_aligned_arrows` | Geen call sites. |
| `renderers/draw_helpers.py:141` | `fill_with_diagonal_hatch` | Geen call sites. |
| `renderers/draw_helpers.py:177` | `draw_moment_symbol` | Geschaduwd door `_draw_moment_symbol` in `section_renderer.py`. Geen call sites. |
| `renderers/draw_helpers.py:225` | `draw_zigzag_line` | Geen call sites. (5 van 6 publieke functies dood — alleen `draw_polygon_on_ax` nog gebruikt.) |
| `utils/geometry.py:183` | `build_layer_polygon` (singular) | Alleen `build_layer_polygons` (plural) gebruikt; `_build_layer_polygon` in `section_renderer.py` is aparte private kopie. |

---

## MEDIUM — Private helpers dood

| Pad | Symbool | Reden |
|---|---|---|
| `app/main_window.py:62` | `_spin` (module-level) | Nergens aangeroepen. |
| `app/main_window.py:403` | `MainWindow._on_process` | Niet verbonden aan knop — "Verwerk"-knop bestaat niet meer. |
| `app/main_window.py:620` | `MainWindow._group_base_name` | Wrapper rond `controller.group_base_name`; nergens aangeroepen. |
| `reporting/builders/damwand_hoofdstuk_builder.py:174` | `_bouw_conclusietabel` | Niet aangeroepen door `build()`; alleen tests. |
| `reporting/builders/damwand_hoofdstuk_builder.py:237` | `_bouw_grafiek_secties` | Niet aangeroepen door `build()`; alleen tests. |
| `ui/scale_slider.py:151` | `ScaleSlider._fmt` | Nergens aangeroepen. |

---

## MEDIUM — Dataclass-velden dood

| Pad | Symbool | Reden |
|---|---|---|
| `parsers/models.py:184` | `Stage.surcharge_loads` | Nooit gevuld door parsers en nooit gelezen. Alleen `surcharge_loads_left`/`_right` zijn in gebruik. |

---

## MEDIUM — Signalen nooit geëmit

| Pad | Symbool | Reden |
|---|---|---|
| `ui/tabs/tab_input_desc.py:62` | `override_changed` | Verbonden in `main_window.py:362` maar nergens `emit()`'ed. Handler `_on_override_changed` en `ReportController.set_text_override` zijn daarmee effectief dood. |

---

## MEDIUM — Dode branches

| Pad | Regel | Probleem |
|---|---|---|
| `renderers/section_renderer.py:968` | — | `'rgba(200,200,255,0.3)' if False else (0.8, 0.8, 1.0, 0.5)` — letterlijke `if False`, eerste tak nooit bereikbaar. |
| `app/report_controller.py:186–196` | — | `build_metadata()` leest niet-bestaande attributen op `ReportState` (zie bug onder HIGH). |

---

## LOW — Niet-gebruikte imports

| Pad | Regel | Symbool |
|---|---|---|
| `app/main_window.py` | 10–14 | `QGridLayout`, `QGroupBox`, `QCheckBox`, `QListWidget`, `QListWidgetItem`, `QSizePolicy`, `QFrame`, `QAbstractItemView` |
| `app/main_window.py` | 23 | `Figure` |
| `parsers/__init__.py` | 4 | `Type` |
| `renderers/draw_helpers.py` | 5 | `numpy as np` |
| `renderers/draw_helpers.py` | 10 | `color_for_matplotlib` |
| `renderers/output_renderer.py` | 14 | `ResultStep` |
| `renderers/output_renderer.py` | 16 | `surface_y_at` |
| `renderers/output_renderer.py` | 18 | `fmt_number` |
| `renderers/section_renderer.py` | 12–15 | `matplotlib`, `matplotlib.pyplot as plt`, `matplotlib.patches as mpatches`, `matplotlib.patheffects as pe` |
| `renderers/section_renderer.py` | 18–19 | `FancyArrow`, `Line2D` |
| `reporting/models.py` | 5 | `Literal` |
| `ui/tabs/tab_report_select.py` | 10 | `ReportItem` |
| `exporters/word_exporter.py` | 195 | `OxmlElement` |

---

## LOW — Niet-gebruikte lokale variabelen

| Pad | Regel | Symbool |
|---|---|---|
| `app/controller.py` | 76, 86 | `loaded` — geteld in `ingest_paths`, nooit gelezen. |
| `renderers/section_renderer.py` | 493, 500 | `best_x` — toegekend maar niet gebruikt. |
| `reporting/builders/result_description_builder.py` | 90 | `fase_naam` — berekend maar nooit gelezen. |
| `ui/tabs/tab_input_desc.py` | 260 | `aantal_data_rijen` — toegekend maar nooit gelezen. |

---

## LOW — Ongebruikte functieparameters

| Pad | Regel | Parameter |
|---|---|---|
| `reporting/builders/result_description_builder.py:85` | `build()` | `step_key` — niet gebruikt in implementatie. |
| `reporting/builders/damwand_hoofdstuk_builder.py:283` | `build()` | `governing_step_key`, `disp_step_key` — niet gebruikt; callers geven `None, None`. |

---

## Overige observaties

- **Parser-registry** (`parsers/__init__.py`): `register_parser`/`get_parser` gedefinieerd maar `AppController.process_files` bypast die volledig en roept `parse_project` rechtstreeks aan. Registry is dode belofte.
- **`renderers/draw_helpers.py`**: 5 van 6 functies dood. `section_renderer.py` heeft eigen private kopieën (`_draw_poly`, `_draw_moment_symbol`, `_draw_zigzag`). Module inkrimpen tot enkel `draw_polygon_on_ax` of consolideren.
- **Drie `build_layer_polygon` varianten**: `utils/geometry.py:183` (dood), `utils/geometry.py:133` (actief, plural), `renderers/section_renderer.py:161` (private kopie). Refactor-target.
- **`_zoek_bodem_punten` duplicaat**: `renderers/vertical_equilibrium_renderer.py:334` en `ui/tabs/tab_verticaal_evenwicht.py:156` zijn identiek. Verplaatsen naar `utils/geometry.py`.

---

## Aanbevolen opruimvolgorde

1. **Verwijder dode modules** — laagste risico, grootste impact:
   `ui/sidebar.py`, `ui/file_list_widget.py`, `ui/controls_panel.py`, `ui/layer_table.py`, `ui/preview_window.py`
   Eventueel ook `exporters/word_exporter.py`, `exporters/excel_exporter.py`, `reporting/builders/html_preview_builder.py` (tests meeverwijderen).

2. **Snoei Excel-pipeline uit `ReportController`**:
   `set_template_excel`, `export_excel`, `build_package`, `build_damwand_sections`, `build_soil_sections`, `build_input_descriptions`, `get_plan` + `template_excel`-veld uit `ReportState`/`ReportPackage`.

3. **Repareer of verwijder `build_metadata`** — nu altijd lege output door ontbrekende attributen.

4. **Snoei `draw_helpers.py`** — verwijder 5 dode functies, consolideer met private helpers in `section_renderer.py`.

5. **Ongebruikte imports / lokale vars / parameters** verwijderen (LOW, veilige clean-up).

6. **Beslis over parser-registry**: gebruiken in `AppController.process_files` of volledig weghalen.
