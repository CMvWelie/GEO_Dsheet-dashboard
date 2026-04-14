# Design: Grondsoortentabel, Damwandbeschrijving en Resultaattabel

**Datum:** 2026-04-14  
**Status:** Goedgekeurd

---

## Overzicht

Drie gerelateerde uitbreidingen van het D-Sheet Dashboard:

1. **Nieuw tabblad "Grondsoortentabel"** — toont grondparameters per profiel (fase-selecteerbaar via dropdown)
2. **Damwandkaart in Invoerbeschrijving** — vaste kaart bovenaan Tab 2B met damwandprofielgegevens
3. **Resultaattabel in Resultaatbeschrijving** — samenvatting van maatgevende rekenresultaten per fase

---

## 1. Datamodel-uitbreidingen (`parsers/models.py`)

### `Soil` — uitgebreid met grondparameters

```python
@dataclass
class Soil:
    name: str
    color: str
    color_int: Optional[int]
    # nieuw:
    gamma_dry: float = 0.0      # SoilGamDry  [kN/m³]
    gamma_wet: float = 0.0      # SoilGamWet  [kN/m³]
    cohesion: float = 0.0       # SoilCohesion [kN/m²]
    phi: float = 0.0            # SoilPhi [°]
    delta: float = 0.0          # SoilDelta [°]
    kh1: float = 0.0            # SoilCurKo1 [kN/m³]
    kh2: float = 0.0            # SoilCurKo2 [kN/m³]
    kh3: float = 0.0            # SoilCurKo3 [kN/m³]
```

### `SheetPilingElement` — uitgebreid met profieleigenschappen

```python
@dataclass
class SheetPilingElement:
    name: str
    x: float
    bottom: float
    top: Optional[float]
    width: float
    segment_top: Optional[float] = None
    segment_bottom: Optional[float] = None
    # nieuw:
    height_mm: float = 0.0              # SheetPilingElementHeight [mm]
    pile_width_mm: float = 0.0          # SheetPilingPileWidth × 1000 [mm]
    ei_knm2_per_m: float = 0.0          # SheetPilingElementEI [kNm²/m]
    section_area_cm2: float = 0.0       # SheetPilingElementSectionArea [cm²/m]
    resisting_moment_cm3: float = 0.0   # SheetPilingElementResistingMoment [cm³/m]
    max_char_moment_knm: float = 0.0    # SheetPilingElementMaxCharacteristicMoment [kNm/m]
    opneembaar_moment_knm: float = 0.0  # max_char_moment × KMod × MaterialFactor × ReductionFactor [kNm/m]
    steel_quality: str = ''             # afgeleid uit elementnaam, bv. "(S240GP)"
```

### `ResultSummary` — nieuw

```python
@dataclass
class ResultSummary:
    stage_number: int
    max_moment_knm: float       # max abs(moment) uit ResultPoint-lijst [kNm/m]
    max_shear_kn: float         # max abs(shear) [kN/m]
    max_disp_mm: float          # max abs(disp) × 1000 [mm]
    mob_moment_pct: float       # max(links, rechts) uit "Max mobilized moment percentage" in SOIL COLLAPSE DATA [%]
    mob_grond_pct: float        # max(links, rechts) uit "Percentage mobilized resistance" in SOIL COLLAPSE DATA [%]
    ondersteuningen: list[tuple[str, float, float]]
    # (naam: str, kracht: float [kN/m], niveau: float [m NAP])
```

### `DamwandCard` — nieuw (in `reporting/builders/input_description_builder.py`)

```python
@dataclass
class DamwandCard:
    profiel: str                            # bv. "AZ 13-700"
    staalkwaliteit: str                     # bv. "S240GP"
    hoogte_mm: float
    breedte_mm: float
    ei_knm2: float
    kopniveau: float                        # [m NAP]
    teenniveau: float                       # [m NAP]
    lengte: float                           # [m]
    ondersteuningen: list[tuple[str, float]]  # (naam, niveau [m NAP])
```

### `Project` — uitgebreid

```python
result_summaries: list[ResultSummary] = field(default_factory=list)
```

---

## 2. Parser-uitbreidingen

### `parsers/shi_parser.py` — `parse_soils()`

Uitbreiden zodat naast naam en kleur ook de numerieke parameters worden uitgelezen:
- `SoilGamDry`, `SoilGamWet`, `SoilCohesion`, `SoilPhi`, `SoilDelta`
- `SoilCurKo1`, `SoilCurKo2`, `SoilCurKo3` → respectievelijk `kh1`, `kh2`, `kh3`

### `parsers/shi_parser.py` — `parse_sheet_piling()`

Uitbreiden zodat per element ook de extra velden worden gelezen:
- `SheetPilingElementHeight`, `SheetPilingPileWidth` (× 1000 → mm)
- `SheetPilingElementEI`, `SheetPilingElementSectionArea`, `SheetPilingElementResistingMoment`
- `SheetPilingElementMaxCharacteristicMoment`
- `SheetPilingElementKMod`, `SheetPilingElementMaterialFactor`, `sSheetPilingElementReductionFactorMaxMoment` → `opneembaar_moment_knm = max_char × kmod × mat_factor × red_factor`
- `steel_quality` wordt afgeleid door de regex `\(([^)]+)\)` toe te passen op de elementnaam

### `parsers/shd_parser.py` — `parse_result_summaries()`

Nieuwe functie die per `[CONSTRUCTION STAGE]` blok:
- `StageNumber` uitleest
- `SOIL COLLAPSE DATA` doorzoekt op "Percentage mobilized resistance" (links en rechts gemiddeld of max) en "mobilized moment percentage" (links en rechts)
- `ANCHOR DATA` tabel doorzoekt op ankerkrachten per ondersteuning
- `ResultStage.points` gebruikt voor max moment/kracht/verplaatsing

Resultaat opgeslagen in `Project.result_summaries`.

---

## 3. Nieuw tabblad: `ui/tabs/tab_grondsoorten.py`

### `TabGrondsoorten(QWidget)`

**Layout (van boven naar beneden):**
1. Toolbar-balk met label "Profiel:" en `QComboBox` (`_profiel_combo`)
2. Gestylde tabel met kolommen:

   | BK laag [m NAP] | OK laag [m NAP] | Laag | γd [kN/m³] | γn [kN/m³] | c'kar [kN/m²] | φ'kar [°] | δ [°] | kh1 | kh2 | kh3 |

3. Voetnoot-sectie met legenda (zoals in Image 1)

**Stijl:** Marine-blauwe header (`#1b3a5c`), zebra-rijen, conform bestaande tabs.

**Publieke API:**
```python
def populate(self, project: Project) -> None: ...
```
Vult de dropdown met profielnamen; toont het eerste profiel direct.

**Interne flow:**
- Dropdown-wijziging → `_on_profiel_changed()` → `_render_profiel(profiel_naam)` → bouwt tabel opnieuw
- Geen `AppController`-aanroep nodig; dit is puur lokale UI-state

**Positie in tab-volgorde:** Na "Doorsnede" (Tab 2A), vóór "Invoerbeschrijving" (Tab 2B).

---

## 4. Damwandkaart in `TabInputDesc`

### Builder-uitbreiding

`InputDescriptionBuilder.build_damwand_card(project: Project) -> DamwandCard | None`

Leest `project.sheet_piling[0]` (indien aanwezig) en `project.anchors`/`project.struts` voor de ondersteuningsniveaus.

### UI-uitbreiding in `TabInputDesc`

Nieuwe methode:
```python
def populate_damwand_card(self, card: DamwandCard | None) -> None: ...
```

- Maakt één kaart bovenaan (vóór alle fase-kaarten) in dezelfde marine-blauwe stijl
- Kaartinhoud conform Image 2: Profiel, Staalkwaliteit, Hoogte h, Breedte b, E-modulus staal, Kopniveau, Teenniveau, Lengte, Niveau ondersteuning 1, Niveau ondersteuning 2
- Indien `card is None`: geen kaart tonen

Aanroep in `main_window.py` samen met de bestaande `populate_fase_cards()` aanroep.

---

## 5. Resultaattabel in `TabResultDesc`

### UI-uitbreiding in `TabResultDesc`

Nieuwe methode:
```python
def populate_resultaat_tabel(self, project: Project, stage_idx: int) -> None: ...
```

- Voegt een styled sectie toe aan de bestaande scroll-inhoud
- Tabelkolommen conform Image 3: Specificaties | Doorsnede 1 | Eenheid
- Rijen: Profiel, Staalkwaliteit, Opneembaar moment, Niveau b.k./o.k., Damwandlengte, Moment Msd, Dwarskracht Dsd, Gemobiliseerd Moment %, Gemobiliseerd Grond %, Verplaatsing urep BGT, Ondersteuning 1 (naam + kracht + niveau), Ondersteuning 2 (naam + kracht + niveau)
- Combo-box bovenaan de tab voor fase-selectie
- Leest uit `project.result_summaries[stage_idx]` en `project.sheet_piling[0]`

---

## 6. Wiring in `main_window.py`

- `tab_grondsoorten` toegevoegd na `tab_input_view`
- `_update_all()` / `_on_main_tab_changed()` vernieuwen grondsoortentabel en resultaattabel
- `populate_damwand_card()` aangeroepen samen met `populate_fase_cards()`
- `result_summaries` worden gevuld tijdens `AppController.process_files()`

---

## Niet in scope

- Hoek lijf met horizontaal (niet aanwezig in .shd, zou een hardcoded profieltabel vereisen)
- Export van de grondsoortentabel naar Excel/Word (aparte taak)
- Meerdere damwand-secties (huidig model: één sectie per project)
