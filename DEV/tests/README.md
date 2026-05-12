# Tests

Pytest-suite voor parsers, rapportage-builders, exporters, app-instellingen, thema's en de aanvullende-berekeningen-tabs. Tests gebruiken embedded `SAMPLE_SHD`-strings — er zijn geen externe testbestanden nodig.

## Uitvoeren

```bash
pytest -v                                          # alle tests
pytest DEV/tests/test_parsers.py -v                    # één module
pytest DEV/tests/test_parsers.py::test_parse_soils -v  # één test
```

Installeer eerst de dev-afhankelijkheden:

```bash
pip install -r DEV/requirements-dev.txt
```

## Bestanden

| Bestand | Scope |
|---|---|
| `conftest.py` | Gedeelde fixtures (o.a. `qapp` voor Qt-tests, voorbeeld-`Project` factories). |
| `test_parsers.py` | Volledige parser-pijplijn met embedded SHD-strings: soils, soil_profiles, sheet_piling, anchors, struts, water_levels, surfaces, stages en `parse_project`. |
| `test_app_settings.py` | Persistentie van `RenderSettings`/`ViewportSettings`/`AppSettings` via `ConfigManager`. |
| `test_app_settings_theme.py` | Opslaan en laden van `active_theme_name` in `AppSettings`. |
| `test_theme.py` | `Theme`-dataclass, JSON-loader, `discover_themes()` en `Theme.build_stylesheet()`. |
| `test_damwand_hoofdstuk_builder.py` | Bouw van het complete damwand-hoofdstuk uit project + grondprofielen. |
| `test_soil_table_builder.py` | Grondsoortentabel-builder: rijen, kolommen, sortering. |
| `test_result_description_builder.py` | Resultaatbeschrijving (CUR 166-stappen 6.1 t/m 6.5) en `TextBlock`-overrides. |
| `test_word_hoofdstuk_exporter.py` | Word-hoofdstuk-export: paragraafstijlen, tabellen, afbeeldingen. |
| `test_hydraulische_grondbreuk.py` | Berekening en weergave van hydraulische grondbreuk-controle. |
| `test_verticaal_evenwicht.py` | Berekening en renderer van verticaal evenwicht. |
| `test_tab_result_desc.py` | UI-gedrag van de Resultaatbeschrijving-tab (overrides, refresh). |
| `test_tab_input_desc.py` | UI-gedrag van de Invoerbeschrijving-tab (opbouw, overrides). |
| `test_tab_grondsoorten.py` | UI-gedrag van de Grondsoortentabel-tab (weergave, selectie). |
| `test_debug_tab.py` | Debug-tab: invoer- en uitvoerinspectie. |
| `test_input_description_builder.py` | `InputDescriptionBuilder`: fasekaarten, damwandkaart en `TextBlock`-inhoud. |
| `test_report_controller.py` | `ReportController`: rapportagepijplijn, secties en export-orkestratie. |
| `test_app_controller_render.py` | `AppController`: foutafhandeling bij render-aanroepen. |
| `test_docx_to_pdf_converter.py` | `DocxToPdfConverter`: conversie via Word COM en LibreOffice-fallback. |

## Patronen

- **Embedded testdata**: parser-tests gebruiken `SAMPLE_SHD` strings i.p.v. losse bestanden — de tests blijven daardoor zelfstandig en snel.
- **Gedeelde fixtures**: `conftest.py` levert factory-fixtures voor `Project`, `Stage` en grondlagen die in meerdere builder-tests hergebruikt worden.
- **Qt-tests**: tests die widgets instantiëren gebruiken een `qapp`-fixture die één keer per sessie een `QApplication` aanmaakt; widgets worden niet getoond, alleen geconstrueerd en gequeryd.
- **Geen mocks van databronnen**: bouw liever een minimaal `Project` op dan een mock — dat houdt de tests dicht bij echte uitvoer.

