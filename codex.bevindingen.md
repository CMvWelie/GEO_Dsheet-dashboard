# Codex bevindingen dode-code-analyse

Datum: 2026-05-07

## Conclusie

`dode_code_analyse.md` klopt grotendeels voor productiegebruik, maar bevat een paar duidelijke false positives. Niet alles wat daarin als dood staat kan blind worden verwijderd.

## Correcties op de analyse

- `app/report_controller.py:186` - `build_metadata()` is niet dood. `export_word()` roept deze methode aan rond regel 227. De bugmelding klopt wel: `build_metadata()` leest `project_name`, `client`, `author`, enz. direct van `ReportState`, terwijl de echte data in `ReportState.metadata` zit.
- `parsers/models.py:184` - `Stage.surcharge_loads` is niet dood. De parser vult dit veld in `parsers/shi_parser.py` en de debug-invoertab leest het in `ui/tabs/tab_debug_invoer.py`. Die debug-tab is onderdeel van de app via `TabInstellingen`.
- `exporters/excel_exporter.py` wordt nog geimporteerd en geinstantieerd door `ReportController`. De enige functionele route lijkt wel `ReportController.export_excel()`, en die wordt niet vanuit de huidige UI aangeroepen.
- `exporters/word_exporter.py` en `reporting/builders/html_preview_builder.py` lijken niet meer in de productie-app gebruikt te worden, maar tests importeren ze nog wel. Tests moeten dus mee worden aangepast of verwijderd als deze modules verdwijnen.

## Waarschijnlijk wel dood in productie

- `ui/sidebar.py`
- `ui/file_list_widget.py` - alleen gebruikt door `ui/sidebar.py`
- `ui/controls_panel.py`
- `ui/layer_table.py`
- `ui/preview_window.py` - vervangen door `ui/word_pdf_preview_window.py`
- Oude Excel/package-pipeline in `ReportController`: `set_template_excel`, `export_excel`, `build_package`, `build_damwand_sections`, `build_soil_sections`, `build_input_descriptions`, `get_plan`
- Parser-registry in `parsers/__init__.py`: `get_parser()` wordt niet gebruikt; `AppController.process_files()` roept `parse_project()` direct aan.
- In `renderers/draw_helpers.py` lijken alle publieke helpers behalve `draw_polygon_on_ax()` ongebruikt.

## Aanpakadvies

1. Verwijder eerst de ongeimporteerde UI-modules. Dat is de laagste-risico opruiming.
2. Repareer `ReportController.build_metadata()` voordat aan Word-export wordt gesnoeid.
3. Ruim de oude Excel/package-pipeline apart op en werk bijbehorende tests/docs mee bij.
4. Verwijder `Stage.surcharge_loads` niet zonder eerst de debug-tab en parsergedrag bewust aan te passen.
5. Als `WordExporter` en `HtmlPreviewBuilder` verdwijnen, verwijder of herschrijf ook de bijbehorende tests.
