# D-Sheet Dashboard

PyQt6 desktop applicatie voor het visualiseren en analyseren van **D-Sheet damwand (sheet pile wall) geotechnische berekeningen**. Leest `.shd` bestanden (Deltares D-Sheet uitvoer) en biedt doorsnede-visualisatie, resultaatgrafieken, invoerbeschrijvingen en export naar Excel en Word.

Ontwikkeld door **DKIB Geotechniek**.

---

## Inhoud

- [Functionaliteit](#functionaliteit)
- [Technologieën](#technologieën)
- [Vereisten](#vereisten)
- [Installatie en opstarten](#installatie-en-opstarten)
- [Gebruik](#gebruik)
- [Architectuur](#architectuur)
- [Mapstructuur](#mapstructuur)
- [Configuratie](#configuratie)
- [Rapportage en export](#rapportage-en-export)
- [Tests uitvoeren](#tests-uitvoeren)
- [Nieuwe parser toevoegen](#nieuwe-parser-toevoegen)
- [Ontwikkelen](#ontwikkelen)
- [Domeinkennis](#domeinkennis)

---

## Functionaliteit

- Importeren en parsen van `.shd` D-Sheet bestanden (drag-and-drop of bestandsdialoog)
- Beheer van meerdere projecten tegelijk binnen één sessie
- Fase-afhankelijke doorsnede-visualisatie — grondlagen, waterpeilen, ankers, stempels, veren, belastingen en normaalkrachten
- Resultaatgrafieken — moment, dwarskracht en verplaatsing per fase en VERIFY STEP
- Invoerbeschrijving en resultaatbeschrijving als gestructureerde tekst met handmatige tekstoverrides
- Rapportage-export naar Excel (`.xlsx`) en Word (`.docx`) via optionele templates met JSON-sidecar mapping
- Pre-export validatie van rapportmetadata, geselecteerde items en templatepaden
- Configuratieopslag per gebruiker in `~/.dsheet_dashboard/config.json`
- Export van figuren als PNG

---

## Technologieën

| Pakket | Versie | Gebruik |
|---|---|---|
| Python | **3.10+** | Taal (vereist voor `str \| None` union-syntax) |
| PyQt6 | ≥ 6.4 | GUI framework (fallback: PySide6) |
| matplotlib | ≥ 3.7 | Doorsnede- en resultaatgrafieken |
| numpy | ≥ 1.24 | Numerieke berekeningen |
| openpyxl | ≥ 3.1 | Excel export (optioneel, alleen nodig bij Excel-export) |
| python-docx | ≥ 1.0 | Word export (optioneel, alleen nodig bij Word-export) |
| pytest | ≥ 7.0 | Unit tests |

---

## Vereisten

- Python **3.10** of hoger
- PyQt6 of PySide6 (PyQt6 heeft de voorkeur)
- Runtime-afhankelijkheden staan in `requirements.txt`; testpakketten in `DEV/requirements-dev.txt`
- `openpyxl`, `python-docx` en `numpy` zijn verplicht en worden bij app-start gecontroleerd in `run.pyw`

---

## Installatie en opstarten

```bash
cd Dsheet_dashboard
pip install -r requirements.txt           # runtime
pip install -r DEV/requirements-dev.txt       # incl. tests
python run.pyw
```

Bij het opstarten wordt automatisch gecontroleerd of PyQt6 beschikbaar is. Als PyQt6 niet aanwezig is, valt de applicatie terug op PySide6. Als geen van beide geïnstalleerd is, verschijnt een duidelijke foutmelding met het installatiecommando.

---

## Gebruik

### Bestanden importeren

1. Open de tab **Rapportcontext** — dit is de gecombineerde import- en metadata-tab.
2. Sleep `.shd` bestanden naar het dropgebied, of klik op **Importeer…** om een bestandsdialoog te openen.
3. Klik op **Verwerk** om de bestanden te parsen. Elk `.shd` bestand wordt als één project gegroepeerd in een `FileBundle`.
4. Geslaagde projecten verschijnen in de lijst **Ingeladen projecten**. Klik op een project om het te selecteren.

### Doorsnede en grondsoorten

- Tab **Doorsnede**: matplotlib-visualisatie van damwand, grondlagen, waterpeilen, ankers, stempels, veren en belastingen voor de geselecteerde fase.
- Tab **Grondsoortentabel**: tabeloverzicht van alle grondsoorten met selectie- en exportopties.

### Resultaten bekijken

De tab **Resultaten** toont grafieken van moment, dwarskracht en verplaatsing. Selecteer een VERIFY STEP en fase via de keuzelijsten.

### Beschrijvingen

- **Invoerbeschrijving**: gestructureerde tekst over de invoerdata van het actieve project en de geselecteerde fase.
- **Resultaatbeschrijving**: gestructureerde tekst over de berekeningsresultaten.

Tekst in beide beschrijvingen kan handmatig worden overschreven via **TextBlock overrides** (opgeslagen in `ReportState.overrides`).

### Aanvullende berekeningen

De tab **Aanvullende berekeningen** bevat subtabs voor extra geotechnische controles: **Hydraulische Grondbreuk** en **Verticaal evenwicht**.

### Rapportage aanmaken

1. Vul de rapportmetadata in via de tab **Rapportcontext** (projectnaam, opdrachtgever, auteur, datum, revisie).
2. Selecteer en orden de gewenste secties via de tab **Rapportage**, en stel het Word-template-pad in.
3. Exporteer naar Word (`.docx`) of Excel (`.xlsx`) via de export-knoppen in de Rapportage-tab.

### Instellingen en thema's

Open via de knop rechtsboven de verborgen **Instellingen**-tab. Daar kun je render-, viewport- en thema-opties beheren. Thema's zijn JSON-bestanden in de map `themes/` (`dkib.json`, `sixgeoconsult.json`).

---

## Architectuur

**Patroon**: Gecentraliseerde state (`AppState` dataclass) met Qt signals voor reactieve UI updates. Core logica bevat geen Qt imports.

### Datastroom

```
.shd bestanden
  → AppController.ingest_paths()     (tekst inlezen → AppState.raw_files)
  → AppController.process_files()    (groeperen → FileBundle → parse_project → AppState.projects)
  → AppController.render_section()   (SectionRenderer → matplotlib doorsnede figuur)
  → AppController.render_results()   (render_output_charts → moment/kracht/verplaatsingsgrafieken)
  → ReportController.export_word()   (ReportPlan + builders → geselecteerde secties)
  → WordHoofdstukExporter            (ReportSection-lijst → .docx)
```

### Lagen

| Laag | Map | Verantwoordelijkheid |
|---|---|---|
| Applicatie | `app/` | State, controllers, config, viewport; geen Qt imports |
| Parsers | `parsers/` | Bestandsparsing en domain dataclasses |
| Renderers | `renderers/` | matplotlib figuur-generatie; geen Qt imports |
| Rapportage | `reporting/` | Rapportmodellen, builders, plan, validatie; geen Qt imports |
| Exporters | `exporters/` | Word serialisatie |
| UI | `ui/` | PyQt6 widgets; alle Qt imports uitsluitend hier |
| Utils | `utils/` | Hulpfuncties; geen Qt imports |

**Kernregel**: Alleen de `ui/` map mag Qt importeren. Alle andere lagen werken met Python primitives en dataclasses.

### Ontwerppatronen

- **Gecentraliseerde state**: alle state-mutaties gaan via `AppController` of `ReportController`; de view schrijft nooit rechtstreeks naar `AppState`.
- **Geen Qt in controllers**: `AppController`, `ReportController`, `ConfigManager` en `ViewportService` hebben nul Qt-imports.
- **Qt Signals/Slots**: UI-events zijn losjes gekoppeld — widgets emitteren named signals die `main_window.py` verbindt met controller-methoden.
- **BaseRenderer ABC**: nieuwe renderers moeten `renderers.BaseRenderer` subclassen en `render(ax, project, stage, settings, viewport)` implementeren.
- **Parsing**: D-Sheet `.shd` bestanden worden direct via `parsers.shi_parser.parse_project()` verwerkt.
- **Rapportagepijplijn**: `ReportController` (geen Qt) zit tussen UI-tabs en exporters; selecteert secties uit `ReportPlan` en geeft ze door aan `WordHoofdstukExporter`.
- **TextBlock overrides**: `ReportState.overrides` dict koppelt `block_id → override_text`; `TextBlock.effective_text` geeft de override terug als die is ingesteld, anders de gegenereerde tekst.
- **Viewport service**: zoom- en auto-boundslogica zit in `ViewportService`, niet in het venster of de renderer.
- **Configuratiepersistentie**: `ConfigManager` centraliseert alle config I/O op `~/.dsheet_dashboard/config.json`.

---

## Mapstructuur

```
Dsheet_dashboard/
├── run.pyw                            Applicatie-entrypoint
├── requirements.txt                   Runtime-afhankelijkheden
├── app/
│   ├── main_window.py                 QMainWindow: layout en signal-verbindingen
│   ├── state.py                       AppState dataclass (single source of truth)
│   ├── settings.py                    RenderSettings, ViewportSettings, AppSettings
│   ├── controller.py                  AppController: ingest/parse/render/export orkestratie
│   ├── report_controller.py           ReportController: rapportagepijplijn
│   ├── report_state.py                ReportState: actief plan, metadata en overrides
│   ├── config_manager.py              ConfigManager: lees/schrijf ~/.dsheet_dashboard/config.json
│   ├── viewport_service.py            ViewportService: zoom en auto-bounds berekening
│   ├── theme.py                       Theme-dataclass + JSON-loader + QSS-builder
│   ├── theme_apply.py                 bootstrap_theme() en thema-toepassing op QApplication
│   ├── docx_to_pdf_converter.py       DocxToPdfConverter: .docx → .pdf via Word COM of LibreOffice
│   ├── word_preview_worker.py         WordPreviewWorker: QThread-worker voor Word→PDF preview
│   └── restart_session.py             Sessie-overdracht bij herstart (paden bewaren/herstellen)
├── parsers/
│   ├── models.py                      Domain dataclasses (Project, Stage, Soil, etc.)
│   ├── shi_parser.py                  Hoofdparser: parse_project → Project
│   ├── base_parser.py                 Hulpfuncties: extract_section, find_line_value
│   └── __init__.py                    Pakketmarkering
├── renderers/
│   ├── __init__.py                    BaseRenderer ABC
│   ├── section_renderer.py            Doorsnede-visualisatie
│   ├── output_renderer.py             Moment/kracht/verplaatsingsgrafieken
│   ├── vertical_equilibrium_renderer.py  Verticaal-evenwicht visualisatie
│   └── draw_helpers.py                matplotlib tekenprimitieven
├── reporting/
│   ├── models.py                      ReportField, ReportTable, TextBlock, ReportSection, etc.
│   ├── selection.py                   ReportPlan en rapportitemselectie
│   ├── figure_renderer.py             Headless figuurrendering (ReportImageRequest → PNG-bytes)
│   └── builders/
│       ├── input_description_builder.py
│       ├── result_description_builder.py
│       ├── soil_table_builder.py            Grondsoorten-tabelopbouw
│       ├── damwand_hoofdstuk_builder.py     Damwand-hoofdstuk samensteller
│       └── damwand_tekst.py                 Vaste rapportageteksten voor het damwandhoofdstuk
├── exporters/
│   └── word_hoofdstuk_exporter.py     Hoofdstuk-gewijze Word-export
├── ui/
│   ├── info_panel.py
│   ├── scale_slider.py                ScaleSlider widget (API-compatibel met QDoubleSpinBox)
│   ├── status_widget.py               StatusWidget: gekleurde statusbadge (ok/warn/err/idle)
│   ├── word_pdf_preview_window.py      Word/PDF-preview voor rapportage
│   ├── table_styles.py                Centrale tabelopmaak gedreven door thema
│   ├── theme_dialog.py                Dialog voor thema-bewerking
│   └── tabs/
│       ├── tab_report_context.py            Rapportmetadata + bestandsimport (gecombineerd)
│       ├── tab_input_view.py                Doorsnede-weergave (matplotlib canvas)
│       ├── tab_input_desc.py                Invoerbeschrijving als gestructureerde tekst
│       ├── tab_grondsoorten.py              Grondsoortentabel met selectie
│       ├── tab_result_view.py               Resultaatgrafieken (matplotlib canvas)
│       ├── tab_result_desc.py               Resultaatbeschrijving als gestructureerde tekst
│       ├── tab_aanvullende_berekeningen.py  Container voor extra controles
│       ├── tab_hydraulische_grondbreuk.py   Subtab: hydraulische grondbreuk
│       ├── tab_verticaal_evenwicht.py       Subtab: verticaal evenwicht
│       ├── tab_report_select.py             Rapportage-itemselectie + Word-export
│       ├── tab_instellingen.py              Render-, viewport- en thema-instellingen
│       ├── tab_debug.py                     Debug-container (subtabs Invoer/Uitvoer)
│       ├── tab_debug_invoer.py              Debug: ruwe invoerdata-inspectie
│       └── tab_debug_uitvoer.py             Debug: ruwe uitvoerdata-inspectie
├── utils/
│   ├── color_utils.py                 D-Sheet BGR-integer → RGB kleurconversie
│   ├── geometry.py                    Oppervlak-interpolatie, clipping
│   ├── formatting.py                  Nederlandse getalopmaak (komma als decimaalscheidingsteken)
│   └── export_manager.py              PNG/PDF figuur-export
├── themes/
│   ├── dkib.json                      DKIB-thema (huiskleuren, logo, tabelstijlen)
│   └── sixgeoconsult.json             SIX Geoconsult-thema
├── templates/
│   └── damwand_stijlen.docx           Word-template voor rapportage
├── SETUP/
│   ├── maak_snelkoppeling.py         Bureaubladsnelkoppeling aanmaken
│   ├── register_shd.ps1              .shd-bestandsassociatie registreren (PowerShell)
│   └── register_shd.bat              .shd-bestandsassociatie registreren (batch)
└── DEV/
    ├── requirements-dev.txt          Dev/test-afhankelijkheden
    ├── tests/                        Pytest-suite en fixtures
    ├── DEAD/                         Archief van verwijderde dode code
    ├── docs/                         Lokale ontwikkel-/planningsdocumenten
    └── cache/                        Lokale gegenereerde cache-output (genegeerd)
```

---

## Configuratie

Gebruikersinstellingen worden automatisch opgeslagen in `~/.dsheet_dashboard/config.json`. Het bestand bevat drie secties:

```json
{
  "render_settings": {
    "uniform_meters_per_10kpa": 0.5,
    "normal_meters_per_10knm": 0.5,
    "hload_scale": 2.0,
    "moment_radius_meters": 1.0,
    "fs_grondlagen": 9.0,
    "fs_knikpunten": 7.5,
    "fs_waterpeil": 8.0,
    "fs_belastingen": 8.5,
    "fs_constructie": 8.5,
    "fs_damwand": 8.5,
    "fs_assen": 10.0,
    "waterpeil_schaal": 1.0,
    "maaiveld_schaal": 1.0,
    "resultaat_half_breedte_m": 10.0
  },
  "viewport_settings": {
    "auto": true,
    "x_min": -10.0,
    "x_max": 10.0,
    "y_min": -10.0,
    "y_max": 5.0
  },
  "app_settings": {
    "word_template_path": "",
    "standaard_importmap": "",
    "active_theme_name": "DKIB",
    "window_geometry": ""
  }
}
```

Als het bestand ontbreekt of ongeldig is, worden standaardwaarden gebruikt. Het bestand wordt aangemaakt bij de eerste keer opslaan.

---

## Rapportage en export

### Werkwijze

1. Stel rapportmetadata in (tab **Rapportcontext**): verplicht zijn projectnaam, rapporttitel, auteur en datum.
2. Kies en orden de rapportage-items (tab **Rapportage**). Gebruik **Auto-vullen** om secties vanuit de builders voor te laden.
3. Stel per item in of het in Excel, in Word, of in beide terecht moet komen, en geef het Word-templatepad op.
4. Exporteer naar Word of Excel via de export-knoppen in dezelfde tab.

### Templates

Zowel de Excel- als Word-exporter ondersteunen een optioneel template-bestand. Naast het template kan een JSON-sidecar (`.map.json`) worden geplaatst die bepaalt welke cellen of bladwijzers gevuld worden.

**Excel sidecar** (`template.xlsx.map.json`):
```json
{
  "metadata": {
    "project_name": {"sheet": "Voorblad", "cell": "B3"},
    "title":        {"sheet": "Voorblad", "cell": "B5"}
  },
  "sections": {
    "sheet_piling": "Damwand",
    "moment_max":   "Resultaten"
  }
}
```

**Word sidecar** (`template.docx.map.json`):
```json
{
  "metadata": {
    "project_name": "bookmark_project",
    "title":        "bookmark_title"
  },
  "sections": {
    "sheet_piling": "Sectie 2.1 Damwand"
  }
}
```

Zonder template of sidecar worden alle geselecteerde secties als nieuwe werkbladen (Excel) of alinea's (Word) toegevoegd.

---

## Tests uitvoeren

Alle tests uitvoeren:

```bash
pytest -v
```

Een specifieke test-module:

```bash
pytest DEV/tests/test_parsers.py -v
```

Een enkel testgeval:

```bash
pytest DEV/tests/test_parsers.py::test_parse_soils -v
```

De suite dekt parsers (embedded `SAMPLE_SHD` strings — geen externe testbestanden nodig), alle rapportage-builders (`damwand_hoofdstuk`, `input_description`, `result_description`, `soil_table`), de Word-hoofdstuk-exporter, `ReportController`, `AppController` render-foutafhandeling, app-instellingen en thema's, de aanvullende-berekeningen-tabs, diverse UI-tabs (Invoerbeschrijving, Resultaatbeschrijving, Grondsoortentabel, Debug) en `DocxToPdfConverter`. Gedeelde fixtures staan in `DEV/tests/conftest.py`.

---

## Nieuwe parser toevoegen

Maak een parser-functie die `FileBundle` en `base_name` als parameters accepteert en een `Project` dataclass retourneert. De parser mag geen Qt importeren.

```python
# parsers/mijn_parser.py
from parsers.models import FileBundle, Project

def parse_mijn_format(file_bundle: FileBundle, base_name: str) -> Project:
    ...
```

## Ontwikkelen

Codeconventies, naamgeving, PyQt6-patronen, foutafhandeling en terugkerende ontwerppatronen staan gedocumenteerd in [`CLAUDE.md`](CLAUDE.md). Dit bestand is de leidraad voor consistente codebijdragen.

### Kernregels samengevat

- **Geen Qt buiten `ui/`** — controllers, renderers, parsers en utils importeren geen PyQt6
- **State-mutaties via controllers** — de view schrijft nooit rechtstreeks naar `AppState`
- **Type hints verplicht** — elke functie volledig geannoteerd, gebruik `str | None` (niet `Optional`)
- **Nederlands als voertaal** — variabelenamen, commentaar, docstrings en UI-teksten in het Nederlands
- **Dataclasses voor domeinmodellen** — `Project`, `Stage`, `SoilLayer`, instellingen (`RenderSettings`, `ViewportSettings`) etc.
- **Foutafhandeling via returntuples** — `(bool, str)` in controllers, geen exceptions voor herstelbare fouten
- **F-strings altijd** — geen `.format()` of `%`-opmaak

### Nieuwe tab toevoegen

1. Maak `ui/tabs/tab_<naam>.py` aan als `QWidget`-subklasse met een `_build()` methode
2. Instantieer de tab in `app/main_window.py` en voeg toe aan `_main_tabs`
3. Verbind signals in `_connect_signals()` in `main_window.py`
4. Voeg tab-refresh toe in `_on_main_tab_changed()` als inhoud on-demand geladen wordt

---

## Domeinkennis

| Term | Betekenis |
|---|---|
| `.shd` | Deltares D-Sheet uitvoerbestand voor damwandberekeningen |
| m NAP | Normaal Amsterdams Peil (Nederlands hoogtestelsel) |
| GWS | Grondwaterstand |
| Constructiefase | D-Sheet berekent per fase (ontgraving/installatie) de constructieve toestand |
| VERIFY STEP | D-Sheet uitvoerblok met per-fase constructieve resultaten (moment, dwarskracht, verplaatsing) |
| FileBundle | Bundel met de ruwe `.shd` tekst voor één project |
| BGR integer | Windows COLORREF kleurformaat dat D-Sheet gebruikt; `parse_color_int()` converteert naar `rgb(r, g, b)` |
| TextBlock override | Handmatige tekstvervanger; `ReportState.overrides` koppelt `block_id → override_text`; `TextBlock.effective_text` retourneert de override of de gegenereerde tekst |


