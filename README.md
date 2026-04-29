# D-Sheet Dashboard

PyQt6 desktop applicatie voor het visualiseren en analyseren van **D-Sheet damwand (sheet pile wall) geotechnische berekeningen**. Leest `.shi`/`.shd`/`.shs` bestandsformaten (Deltares D-Sheet uitvoer) en biedt doorsnede-visualisatie, resultaatgrafieken, invoerbeschrijvingen en export naar Excel en Word.

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

- Importeren en parsen van `.shi`/`.shd`/`.shs` D-Sheet bestanden (drag-and-drop of bestandsdialoog)
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
- Runtime-afhankelijkheden staan in `requirements.txt`; testpakketten in `requirements-dev.txt`
- `openpyxl` en `python-docx` zijn optioneel — ze worden pas gecontroleerd op het moment van exporteren

---

## Installatie en opstarten

```bash
cd Dsheet_dashboard
pip install -r requirements.txt           # runtime
pip install -r requirements-dev.txt       # incl. tests
python run.pyw
```

Bij het opstarten wordt automatisch gecontroleerd of PyQt6 beschikbaar is. Als PyQt6 niet aanwezig is, valt de applicatie terug op PySide6. Als geen van beide geïnstalleerd is, verschijnt een duidelijke foutmelding met het installatiecommando.

---

## Gebruik

### Bestanden importeren

1. Open de tab **Import**.
2. Sleep `.shi`/`.shd`/`.shs` bestanden naar het dropgebied, of klik op **Importeer…** om een bestandsdialoog te openen.
3. Klik op **Verwerk** om de bestanden te parsen. Bestanden met dezelfde basisnaam (bijv. `project.shi`, `project.shd`, `project.shs`) worden automatisch als één project gegroepeerd in een `FileBundle`.
4. Geslaagde projecten verschijnen in de lijst **Ingeladen projecten**. Klik op een project om het te selecteren.

### Doorsnede bekijken

Ga naar de tab **Doorsnede** om een matplotlib-visualisatie te zien van de damwand, grondlagen, waterpeilen, ankers, stempels, veren en belastingen voor de geselecteerde fase.

### Resultaten bekijken

De tab **Resultaten** toont grafieken van moment, dwarskracht en verplaatsing. Selecteer een VERIFY STEP en fase via de keuzelijsten.

### Beschrijvingen

- **Invoerbeschrijving**: gestructureerde tekst over de invoerdata van het actieve project en de geselecteerde fase.
- **Resultaatbeschrijving**: gestructureerde tekst over de berekeningsresultaten.

Tekst in beide beschrijvingen kan handmatig worden overschreven via **TextBlock overrides** (sla op via de rapportagecontext).

### Rapportage aanmaken

1. Vul de rapportmetadata in via de tab **Rapportcontext** (projectnaam, opdrachtgever, auteur, datum, revisie).
2. Selecteer en orden de gewenste secties via de tab **Rapportinhoud**.
3. Controleer het rapport via de tab **Validatie** (vereist: projectnaam, rapporttitel, auteur, datum).
4. Exporteer via de tab **Export** naar Excel of Word.

---

## Architectuur

**Patroon**: Gecentraliseerde state (`AppState` dataclass) met Qt signals voor reactieve UI updates. Core logica bevat geen Qt imports.

### Datastroom

```
.shi/.shd/.shs bestanden
  → AppController.ingest_paths()     (tekst inlezen → AppState.raw_files)
  → AppController.process_files()    (groeperen → FileBundle → parse_project → AppState.projects)
  → AppController.render_section()   (SectionRenderer → matplotlib doorsnede figuur)
  → AppController.render_results()   (render_output_charts → moment/kracht/verplaatsingsgrafieken)
  → ReportController.build_package() (ReportPlan + builders → ReportPackage)
  → ExcelExporter / WordExporter     (ReportPackage → .xlsx / .docx)
```

### Lagen

| Laag | Map | Verantwoordelijkheid |
|---|---|---|
| Applicatie | `app/` | State, controllers, config, viewport; geen Qt imports |
| Parsers | `parsers/` | Bestandsparsing en domain dataclasses |
| Renderers | `renderers/` | matplotlib figuur-generatie; geen Qt imports |
| Rapportage | `reporting/` | Rapportmodellen, builders, plan, validatie; geen Qt imports |
| Exporters | `exporters/` | Excel en Word serialisatie |
| UI | `ui/` | PyQt6 widgets; alle Qt imports uitsluitend hier |
| Utils | `utils/` | Hulpfuncties; geen Qt imports |

**Kernregel**: Alleen de `ui/` map mag Qt importeren. Alle andere lagen werken met Python primitives en dataclasses.

### Ontwerppatronen

- **Gecentraliseerde state**: alle state-mutaties gaan via `AppController` of `ReportController`; de view schrijft nooit rechtstreeks naar `AppState`.
- **Geen Qt in controllers**: `AppController`, `ReportController`, `ConfigManager` en `ViewportService` hebben nul Qt-imports.
- **Qt Signals/Slots**: UI-events zijn losjes gekoppeld — widgets emitteren named signals die `main_window.py` verbindt met controller-methoden.
- **BaseRenderer ABC**: nieuwe renderers moeten `renderers.BaseRenderer` subclassen en `render(ax, project, stage, settings, viewport)` implementeren.
- **Parser-registry**: nieuw bestandsformaat ondersteunen = `register_parser(ext, fn)` aanroepen in `parsers/__init__.py`.
- **Rapportagepijplijn**: `ReportController` (geen Qt) zit tussen UI-tabs en exporters; bouwt een `ReportPackage` uit `ReportPlan` + builders, dan doorgegeven aan `ExcelExporter` of `WordExporter`.
- **TextBlock overrides**: `ReportState.overrides` dict koppelt `block_id → override_text`; `TextBlock.effective_text` geeft de override terug als die is ingesteld, anders de gegenereerde tekst.
- **Viewport service**: zoom- en auto-boundslogica zit in `ViewportService`, niet in het venster of de renderer.
- **Configuratiepersistentie**: `ConfigManager` centraliseert alle config I/O op `~/.dsheet_dashboard/config.json`.

---

## Mapstructuur

```
Dsheet_dashboard/
├── run.pyw                            Applicatie-entrypoint
├── requirements.txt                   Runtime-afhankelijkheden
├── requirements-dev.txt               Dev/test-afhankelijkheden
├── app/
│   ├── main_window.py                 QMainWindow: layout en signal-verbindingen
│   ├── state.py                       AppState dataclass (single source of truth)
│   ├── settings.py                    RenderSettings, ViewportSettings dataclasses
│   ├── controller.py                  AppController: ingest/parse/render/export orkestratie
│   ├── report_controller.py           ReportController: rapportagepijplijn
│   ├── report_state.py                ReportState: actief plan, metadata en overrides
│   ├── config_manager.py              ConfigManager: lees/schrijf ~/.dsheet_dashboard/config.json
│   └── viewport_service.py            ViewportService: zoom en auto-bounds berekening
├── parsers/
│   ├── models.py                      Domain dataclasses (Project, Stage, Soil, etc.)
│   ├── shi_parser.py                  Hoofdparser (~1058 regels): parse_project → Project
│   ├── base_parser.py                 Hulpfuncties: extract_section, find_line_value
│   └── __init__.py                    Parser plugin registry: register_parser(ext, fn)
├── renderers/
│   ├── __init__.py                    BaseRenderer ABC
│   ├── section_renderer.py            Doorsnede-visualisatie
│   ├── output_renderer.py             Moment/kracht/verplaatsingsgrafieken
│   └── draw_helpers.py                matplotlib tekenprimitieven
├── reporting/
│   ├── models.py                      ReportField, ReportTable, TextBlock, ReportSection, etc.
│   ├── selection.py                   ReportPlan + build_package()
│   ├── validation.py                  ReportValidator → lijst van ValidationIssue
│   └── builders/
│       ├── input_description_builder.py
│       └── result_description_builder.py
├── exporters/
│   ├── excel_exporter.py              ExcelExporter (openpyxl)
│   └── word_exporter.py               WordExporter (python-docx)
├── ui/
│   ├── sidebar.py
│   ├── controls_panel.py
│   ├── info_panel.py
│   ├── layer_table.py
│   ├── file_list_widget.py
│   ├── scale_slider.py                ScaleSlider widget (API-compatibel met QDoubleSpinBox)
│   ├── status_widget.py               StatusWidget: gekleurde statusbadge (ok/warn/err/idle)
│   └── tabs/
│       ├── tab_import.py              Bestandsimport en projectselectie
│       ├── tab_input_view.py          Doorsnede-weergave (matplotlib canvas)
│       ├── tab_input_desc.py          Invoerbeschrijving als gestructureerde tekst
│       ├── tab_result_view.py         Resultaatgrafieken (matplotlib canvas)
│       ├── tab_result_desc.py         Resultaatbeschrijving als gestructureerde tekst
│       ├── tab_report_context.py      Rapportmetadata (opdrachtgever, auteur, datum, etc.)
│       ├── tab_report_select.py       Itemselectie en volgorde voor rapport
│       ├── tab_export.py              Export container (PNG / Excel / Word sub-tabs)
│       ├── tab_excel_export.py        Excel-export sub-tab
│       ├── tab_word_export.py         Word-export sub-tab
│       └── tab_validation.py          Pre-export validatieweergave
├── utils/
│   ├── color_utils.py                 D-Sheet BGR-integer → RGB kleurconversie
│   ├── geometry.py                    Oppervlak-interpolatie, clipping
│   ├── formatting.py                  Nederlandse getalopmaak (komma als decimaalscheidingsteken)
│   └── export_manager.py             PNG/PDF figuur-export
└── tests/
    └── test_parsers.py                Unit tests met embedded testdata
```

---

## Configuratie

Gebruikersinstellingen worden automatisch opgeslagen in `~/.dsheet_dashboard/config.json`. Het bestand bevat twee secties:

```json
{
  "render_settings": {
    "uniform_meters_per_10kpa": 0.5,
    "normal_meters_per_10knm": 0.5,
    "hload_low_scale": 1.0,
    "hload_mid_scale": 2.0,
    "hload_high_scale": 3.0,
    "moment_radius_meters": 1.0,
    "fs_grondlagen": 9.0,
    "fs_knikpunten": 7.5,
    "fs_waterpeil": 8.0,
    "fs_belastingen": 8.5,
    "fs_constructie": 8.5,
    "fs_damwand": 8.5,
    "fs_assen": 10.0,
    "fs_titel": 12.0
  },
  "viewport_settings": {
    "auto": true,
    "x_min": -10.0,
    "x_max": 10.0,
    "y_min": -10.0,
    "y_max": 5.0
  }
}
```

Als het bestand ontbreekt of ongeldig is, worden standaardwaarden gebruikt. Het bestand wordt aangemaakt bij de eerste keer opslaan.

---

## Rapportage en export

### Werkwijze

1. Stel rapportmetadata in (tab **Rapportcontext**): verplicht zijn projectnaam, rapporttitel, auteur en datum.
2. Kies en orden de rapportage-items (tab **Rapportinhoud**). Gebruik **Auto-vullen** om secties vanuit de builders voor te laden.
3. Stel per item in of het in Excel, in Word, of in beide terecht moet komen.
4. Controleer de volledigheid (tab **Validatie**). Fouten zijn rood, waarschuwingen zijn geel.
5. Exporteer via de tab **Export**.

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

```bash
pytest tests/test_parsers.py -v
```

Een enkel testgeval uitvoeren:

```bash
pytest tests/test_parsers.py::test_parse_soils -v
```

De tests gebruiken embedded `SAMPLE_SHI` strings — geen externe testbestanden nodig. De test-suite dekt parsers (`parse_soils`, `parse_soil_profiles`, `parse_sheet_piling`, `parse_anchors`, `parse_struts`, `parse_water_levels`, `parse_surfaces`, `parse_stages`, `parse_project`), kleurconversie (`color_utils`), geometrie (`geometry`) en getalopmaak (`formatting`).

---

## Nieuwe parser toevoegen

Maak een parser-functie die `FileBundle` en `base_name` als parameters accepteert en een `Project` dataclass retourneert. De parser mag geen Qt importeren.

```python
# parsers/mijn_parser.py
from parsers.models import FileBundle, Project

def parse_mijn_format(file_bundle: FileBundle, base_name: str) -> Project:
    ...
```

Registreer de parser in `parsers/__init__.py`:

```python
from parsers.mijn_parser import parse_mijn_format

register_parser(".xyz", parse_mijn_format)
```

---

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
| `.shi` / `.shd` / `.shs` | Deltares D-Sheet uitvoerbestanden voor damwandberekeningen |
| m NAP | Normaal Amsterdams Peil (Nederlands hoogtestelsel) |
| GWS | Grondwaterstand |
| Constructiefase | D-Sheet berekent per fase (ontgraving/installatie) de constructieve toestand |
| VERIFY STEP | D-Sheet uitvoerblok met per-fase constructieve resultaten (moment, dwarskracht, verplaatsing) |
| FileBundle | Groepering van `.shi`, `.shd` en `.shs` bestanden met dezelfde basisnaam |
| BGR integer | Windows COLORREF kleurformaat dat D-Sheet gebruikt; `parse_color_int()` converteert naar `rgb(r, g, b)` |
| TextBlock override | Handmatige tekstvervanger; `ReportState.overrides` koppelt `block_id → override_text`; `TextBlock.effective_text` retourneert de override of de gegenereerde tekst |
