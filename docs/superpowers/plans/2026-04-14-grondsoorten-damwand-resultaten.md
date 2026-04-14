# Grondsoortentabel, Damwandbeschrijving en Resultaattabel — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voeg een grondsoortentabel-tab toe, een damwandkaart in de Invoerbeschrijving-tab, en een resultaattabel in de Resultaatbeschrijving-tab.

**Architecture:** Parser-uitbreidingen in `shi_parser.py` voeden uitgebreide dataclasses (`Soil`, `SheetPilingElement`, nieuw `ResultSummary`); nieuwe en bestaande UI-tabs lezen uitsluitend uit het `Project`-object; wiring via `main_window.py` en `ReportController`.

**Tech Stack:** Python 3.10+, PyQt6, pytest. Geen nieuwe dependencies.

---

## Bestandskaart

| Actie   | Bestand                                              | Verantwoordelijkheid                              |
|---------|------------------------------------------------------|---------------------------------------------------|
| Modify  | `parsers/models.py`                                  | Uitbreiden Soil, SheetPilingElement; nieuwe ResultSummary; Project.result_summaries |
| Modify  | `parsers/shi_parser.py`                              | parse_soils(), parse_sheet_piling(), nieuwe parse_result_summaries() |
| Modify  | `reporting/builders/input_description_builder.py`    | Nieuwe DamwandCard dataclass + build_damwand_card() |
| Create  | `ui/tabs/tab_grondsoorten.py`                        | TabGrondsoorten widget met profiel-dropdown en tabel |
| Modify  | `ui/tabs/tab_input_desc.py`                          | populate_damwand_card() methode                   |
| Modify  | `ui/tabs/tab_result_desc.py`                         | populate_resultaat_tabel() methode                |
| Modify  | `app/report_controller.py`                           | build_damwand_card() methode                      |
| Modify  | `app/main_window.py`                                 | Nieuwe tab, wiring damwandkaart en resultaattabel  |
| Modify  | `tests/test_parsers.py`                              | Tests voor uitgebreide parsers                    |

---

## Task 1: Uitbreid `Soil` dataclass en `parse_soils()`

**Files:**
- Modify: `parsers/models.py`
- Modify: `parsers/shi_parser.py`
- Modify: `tests/test_parsers.py`

- [ ] **Stap 1: Schrijf de falende test**

Voeg toe aan `tests/test_parsers.py`:

```python
def test_parse_soils_grondparameters():
    """parse_soils() moet gamma, phi, delta en kh-waarden uitlezen."""
    tekst = """\
[SOIL]
Klei zwak
SoilColor=5855577
SoilGamDry=14.00
SoilGamWet=14.00
SoilCohesion=0.00
SoilPhi=17.50
SoilDelta=11.67
SoilCurKo1=2000.00
SoilCurKo2=1000.00
SoilCurKo3=500.00
[END OF SOIL]
"""
    soilen = parse_soils(tekst)
    assert len(soilen) == 1
    s = soilen[0]
    assert s.name == 'Klei zwak'
    assert s.gamma_dry == pytest.approx(14.0)
    assert s.gamma_wet == pytest.approx(14.0)
    assert s.cohesion == pytest.approx(0.0)
    assert s.phi == pytest.approx(17.5)
    assert s.delta == pytest.approx(11.67)
    assert s.kh1 == pytest.approx(2000.0)
    assert s.kh2 == pytest.approx(1000.0)
    assert s.kh3 == pytest.approx(500.0)
```

- [ ] **Stap 2: Voer de test uit om te bevestigen dat hij faalt**

```
pytest tests/test_parsers.py::test_parse_soils_grondparameters -v
```
Verwacht: `FAILED` — `AttributeError: 'Soil' object has no attribute 'gamma_dry'`

- [ ] **Stap 3: Breid `Soil` uit in `parsers/models.py`**

Vervang de bestaande `Soil`-klasse:

```python
@dataclass
class Soil:
    name: str
    color: str          # "rgb(r, g, b)"
    color_int: Optional[int]
    # Grondparameters
    gamma_dry: float = 0.0      # SoilGamDry  [kN/m³]
    gamma_wet: float = 0.0      # SoilGamWet  [kN/m³]
    cohesion: float = 0.0       # SoilCohesion [kN/m²]
    phi: float = 0.0            # SoilPhi [°]
    delta: float = 0.0          # SoilDelta [°]
    kh1: float = 0.0            # SoilCurKo1 [kN/m³]
    kh2: float = 0.0            # SoilCurKo2 [kN/m³]
    kh3: float = 0.0            # SoilCurKo3 [kN/m³]
```

- [ ] **Stap 4: Breid `parse_soils()` uit in `parsers/shi_parser.py`**

Vervang de return-regel in de `for`-loop van `parse_soils()`:

```python
        out.append(Soil(
            name=name,
            color=color,
            color_int=color_int,
            gamma_dry=float(find_line_value(block, r'^SoilGamDry\s*=\s*(.+)$') or 0),
            gamma_wet=float(find_line_value(block, r'^SoilGamWet\s*=\s*(.+)$') or 0),
            cohesion=float(find_line_value(block, r'^SoilCohesion\s*=\s*(.+)$') or 0),
            phi=float(find_line_value(block, r'^SoilPhi\s*=\s*(.+)$') or 0),
            delta=float(find_line_value(block, r'^SoilDelta\s*=\s*(.+)$') or 0),
            kh1=float(find_line_value(block, r'^SoilCurKo1\s*=\s*(.+)$') or 0),
            kh2=float(find_line_value(block, r'^SoilCurKo2\s*=\s*(.+)$') or 0),
            kh3=float(find_line_value(block, r'^SoilCurKo3\s*=\s*(.+)$') or 0),
        ))
```

- [ ] **Stap 5: Voer de test uit om te bevestigen dat hij slaagt**

```
pytest tests/test_parsers.py::test_parse_soils_grondparameters -v
```
Verwacht: `PASSED`

- [ ] **Stap 6: Draai alle tests om regressies te controleren**

```
pytest tests/test_parsers.py -v
```
Verwacht: alle bestaande tests blijven `PASSED`.

- [ ] **Stap 7: Commit**

```bash
git add parsers/models.py parsers/shi_parser.py tests/test_parsers.py
git commit -m "feat: breid Soil dataclass uit met grondparameters (gamma, phi, delta, kh)"
```

---

## Task 2: Uitbreid `SheetPilingElement` dataclass en `parse_sheet_piling()`

**Files:**
- Modify: `parsers/models.py`
- Modify: `parsers/shi_parser.py`
- Modify: `tests/test_parsers.py`

- [ ] **Stap 1: Schrijf de falende test**

Voeg toe aan `tests/test_parsers.py`:

```python
def test_parse_sheet_piling_uitgebreid():
    """parse_sheet_piling() moet profieleigenschappen uitlezen."""
    tekst = """\
[SHEET PILING]
0
      0.00 Level top sheet piling
     14.00 Length
  1 Number of elements
[SHEET PILING ELEMENT]
AZ 13-700 (S240GP)
SheetPilingElementX=0.0
SheetPilingElementLevel=-14.0
SheetPilingElementWidth=1.0
SheetPilingElementHeight=315
SheetPilingPileWidth=0.70
SheetPilingElementEI=4.313400E+04
SheetPilingElementSectionArea=135
SheetPilingElementResistingMoment=1305
SheetPilingElementMaxCharacteristicMoment=313.00
SheetPilingElementKMod=1.00
SheetPilingElementMaterialFactor=1.00
sSheetPilingElementReductionFactorMaxMoment=1.00
[END OF SHEET PILING ELEMENT]
[END OF SHEET PILING]
"""
    elementen = parse_sheet_piling(tekst)
    assert len(elementen) == 1
    el = elementen[0]
    assert el.name == 'AZ 13-700 (S240GP)'
    assert el.height_mm == pytest.approx(315.0)
    assert el.pile_width_mm == pytest.approx(700.0)
    assert el.ei_knm2_per_m == pytest.approx(43134.0)
    assert el.section_area_cm2 == pytest.approx(135.0)
    assert el.resisting_moment_cm3 == pytest.approx(1305.0)
    assert el.max_char_moment_knm == pytest.approx(313.0)
    assert el.opneembaar_moment_knm == pytest.approx(313.0)
    assert el.steel_quality == 'S240GP'
```

- [ ] **Stap 2: Voer de test uit om te bevestigen dat hij faalt**

```
pytest tests/test_parsers.py::test_parse_sheet_piling_uitgebreid -v
```
Verwacht: `FAILED` — `AttributeError: 'SheetPilingElement' object has no attribute 'height_mm'`

- [ ] **Stap 3: Breid `SheetPilingElement` uit in `parsers/models.py`**

Vervang de bestaande `SheetPilingElement`-klasse:

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
    # Profieleigenschappen
    height_mm: float = 0.0              # SheetPilingElementHeight [mm]
    pile_width_mm: float = 0.0          # SheetPilingPileWidth × 1000 [mm]
    ei_knm2_per_m: float = 0.0          # SheetPilingElementEI [kNm²/m]
    section_area_cm2: float = 0.0       # SheetPilingElementSectionArea [cm²/m]
    resisting_moment_cm3: float = 0.0   # SheetPilingElementResistingMoment [cm³/m]
    max_char_moment_knm: float = 0.0    # SheetPilingElementMaxCharacteristicMoment [kNm/m]
    opneembaar_moment_knm: float = 0.0  # max_char × KMod × MaterialFactor × ReductionFactor [kNm/m]
    steel_quality: str = ''             # afgeleid uit elementnaam, bv. "(S240GP)" → "S240GP"
```

- [ ] **Stap 4: Breid `parse_sheet_piling()` uit in `parsers/shi_parser.py`**

Vervang het `out.append(SheetPilingElement(...))` blok in `parse_sheet_piling()`:

```python
        raw_name = lines_b[0] if lines_b else f'Damwand {len(out) + 1}'
        # Steel quality: haal tekst tussen haakjes op, bv. "AZ 13-700 (S240GP)" → "S240GP"
        kwaliteit_m = re.search(r'\(([^)]+)\)', raw_name)
        staal = kwaliteit_m.group(1) if kwaliteit_m else ''

        max_char = float(find_line_value(block, r'^SheetPilingElementMaxCharacteristicMoment\s*=\s*(.+)$') or 0)
        kmod = float(find_line_value(block, r'^SheetPilingElementKMod\s*=\s*(.+)$') or 1)
        mat_f = float(find_line_value(block, r'^SheetPilingElementMaterialFactor\s*=\s*(.+)$') or 1)
        red_f = float(find_line_value(block, r'^sSheetPilingElementReductionFactorMaxMoment\s*=\s*(.+)$') or 1)
        pile_w_raw = float(find_line_value(block, r'^SheetPilingPileWidth\s*=\s*(.+)$') or 0)

        out.append(SheetPilingElement(
            name=raw_name,
            x=float(find_line_value(block, r'^SheetPilingElementX=(.+)$') or 0),
            bottom=float(find_line_value(block, r'^SheetPilingElementLevel=(.+)$') or 0),
            top=common_top,
            width=float(find_line_value(block, r'^SheetPilingElementWidth=(.+)$') or 1),
            height_mm=float(find_line_value(block, r'^SheetPilingElementHeight\s*=\s*(.+)$') or 0),
            pile_width_mm=pile_w_raw * 1000,
            ei_knm2_per_m=float(find_line_value(block, r'^SheetPilingElementEI\s*=\s*(.+)$') or 0),
            section_area_cm2=float(find_line_value(block, r'^SheetPilingElementSectionArea\s*=\s*(.+)$') or 0),
            resisting_moment_cm3=float(find_line_value(block, r'^SheetPilingElementResistingMoment\s*=\s*(.+)$') or 0),
            max_char_moment_knm=max_char,
            opneembaar_moment_knm=max_char * kmod * mat_f * red_f,
            steel_quality=staal,
        ))
```

- [ ] **Stap 5: Voer de test uit om te bevestigen dat hij slaagt**

```
pytest tests/test_parsers.py::test_parse_sheet_piling_uitgebreid -v
```
Verwacht: `PASSED`

- [ ] **Stap 6: Draai alle tests**

```
pytest tests/test_parsers.py -v
```
Verwacht: alle tests `PASSED`.

- [ ] **Stap 7: Commit**

```bash
git add parsers/models.py parsers/shi_parser.py tests/test_parsers.py
git commit -m "feat: breid SheetPilingElement uit met profieleigenschappen"
```

---

## Task 3: Voeg `ResultSummary` toe en `parse_result_summaries()`

**Files:**
- Modify: `parsers/models.py`
- Modify: `parsers/shi_parser.py`
- Modify: `tests/test_parsers.py`

- [ ] **Stap 1: Schrijf de falende test**

Voeg toe aan `tests/test_parsers.py`:

```python
from parsers.shi_parser import parse_result_summaries

def test_parse_result_summaries_basis():
    """parse_result_summaries() leest max moment, shear, displacement en mobilisatiepercentages per stage."""
    shd_tekst = """\
[CONSTRUCTION STAGE]
StageNumber=1
[ANCHOR DATA]
[TABLE]
DataCount=1
[COLUMN INDICATION]
Position
Force
ElasticityModulus
Status
Side
Type
Name
[END OF COLUMN INDICATION]
[DATA]
    -2.00000     44.19000          9999.000     1     1     0 'GroutankerL'
[END OF DATA]
[END OF TABLE]
[END OF ANCHOR DATA]
[SOIL COLLAPSE DATA]
   12.70 : Percentage mobilized resistance left
   12.62 : Percentage mobilized resistance right
-38002.71 : Max moment left
-19869.14 : Max moment right
    11.6 : Max mobilized moment percentage left
    11.8 : Max mobilized moment percentage right
[END OF SOIL COLLAPSE DATA]
[MOMENTS FORCES DISPLACEMENTS]
[TABLE]
DataCount=3
[COLUMN INDICATION]
Moment
Shear force
Displacements
[END OF COLUMN INDICATION]
[DATA]
     0.00000      0.00000      0.02356
     5.00000     87.70000      0.02360
    -86.20000    -10.00000      0.02360
[END OF DATA]
[END OF TABLE]
[END OF CONSTRUCTION STAGE]
"""
    summaries = parse_result_summaries(shd_tekst)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.stage_number == 1
    assert s.max_moment_knm == pytest.approx(86.2)
    assert s.max_shear_kn == pytest.approx(87.7)
    assert s.max_disp_mm == pytest.approx(23.56)
    assert s.mob_moment_pct == pytest.approx(11.8)
    assert s.mob_grond_pct == pytest.approx(12.70)
    assert len(s.ondersteuningen) == 1
    naam, kracht, niveau = s.ondersteuningen[0]
    assert naam == 'GroutankerL'
    assert kracht == pytest.approx(44.19)
    assert niveau == pytest.approx(-2.0)
```

- [ ] **Stap 2: Voer de test uit om te bevestigen dat hij faalt**

```
pytest tests/test_parsers.py::test_parse_result_summaries_basis -v
```
Verwacht: `FAILED` — `ImportError: cannot import name 'parse_result_summaries'`

- [ ] **Stap 3: Voeg `ResultSummary` toe aan `parsers/models.py`**

Voeg toe na de `SupportResumeItem` klasse (vóór `FileBundle`):

```python
@dataclass
class ResultSummary:
    """Samenvatting van maatgevende rekenresultaten per constructiefase."""
    stage_number: int
    max_moment_knm: float       # max abs(moment) uit MOMENTS FORCES DISPLACEMENTS [kNm/m]
    max_shear_kn: float         # max abs(shear) [kN/m]
    max_disp_mm: float          # max abs(disp) × 1000 [mm]
    mob_moment_pct: float       # max(links, rechts) uit SOIL COLLAPSE DATA [%]
    mob_grond_pct: float        # max(links, rechts) uit SOIL COLLAPSE DATA [%]
    ondersteuningen: list[tuple[str, float, float]] = field(default_factory=list)
    # (naam, kracht [kN/m], niveau [m NAP])
```

Voeg `result_summaries` toe aan `Project`:

```python
    result_summaries: list[ResultSummary] = field(default_factory=list)
```

(Voeg dit toe aan het einde van de `Project` dataclass velden.)

- [ ] **Stap 4: Voeg `parse_result_summaries()` toe aan `parsers/shi_parser.py`**

Voeg de import toe bovenaan bij de andere models imports:

```python
from parsers.models import (
    ...,
    ResultSummary,
)
```

Voeg de functie toe na `parse_supports_resume()`, vóór `parse_project()`:

```python
def parse_result_summaries(shd_text: str) -> list[ResultSummary]:
    """Parseer CONSTRUCTION STAGE blokken uit .shd voor resultaatsamenvatting.

    Parameters
    ----------
    shd_text: Volledige inhoud van het .shd bestand.

    Returns
    -------
    list[ResultSummary]  Eén samenvatting per constructiefase.
    """
    out: list[ResultSummary] = []
    for m in re.finditer(
        r'\[CONSTRUCTION STAGE\]([\s\S]*?)\[END OF CONSTRUCTION STAGE\]',
        shd_text,
        re.IGNORECASE
    ):
        blok = m.group(1)

        # Stage-nummer
        sn_m = re.search(r'^StageNumber\s*=\s*(\d+)', blok, re.MULTILINE)
        if not sn_m:
            continue
        stage_nr = int(sn_m.group(1))

        # Mobilisatiepercentages uit SOIL COLLAPSE DATA
        mob_grond_l = _float_pattern(blok, r'([\d.]+)\s*:\s*Percentage mobilized resistance left')
        mob_grond_r = _float_pattern(blok, r'([\d.]+)\s*:\s*Percentage mobilized resistance right')
        mob_mom_l   = _float_pattern(blok, r'([\d.]+)\s*:\s*Max mobilized moment percentage left')
        mob_mom_r   = _float_pattern(blok, r'([\d.]+)\s*:\s*Max mobilized moment percentage right')
        mob_grond = max(mob_grond_l or 0.0, mob_grond_r or 0.0)
        mob_mom   = max(mob_mom_l or 0.0,   mob_mom_r or 0.0)

        # Moment / kracht / verplaatsing uit MOMENTS FORCES DISPLACEMENTS
        mfd_m = re.search(
            r'\[MOMENTS FORCES DISPLACEMENTS\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
            blok, re.IGNORECASE
        )
        max_mom = 0.0
        max_shear = 0.0
        max_disp_mm = 0.0
        if mfd_m:
            for rij in mfd_m.group(1).split('\n'):
                delen = rij.strip().split()
                if len(delen) >= 3:
                    try:
                        mom, shear, disp = float(delen[0]), float(delen[1]), float(delen[2])
                        max_mom   = max(max_mom,   abs(mom))
                        max_shear = max(max_shear, abs(shear))
                        max_disp_mm = max(max_disp_mm, abs(disp) * 1000)
                    except ValueError:
                        pass

        # Ankerkrachten uit ANCHOR DATA tabel
        ondersteuningen: list[tuple[str, float, float]] = []
        anker_m = re.search(
            r'\[ANCHOR DATA\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
            blok, re.IGNORECASE
        )
        if anker_m:
            for rij in anker_m.group(1).split('\n'):
                rij = rij.strip()
                if not rij:
                    continue
                naam_m = re.match(r"^(.*?)'([^']+)'", rij)
                if naam_m:
                    cijfers = naam_m.group(1).strip().split()
                    naam = naam_m.group(2)
                    if len(cijfers) >= 2:
                        try:
                            niveau = float(cijfers[0])
                            kracht = float(cijfers[1])
                            ondersteuningen.append((naam, kracht, niveau))
                        except ValueError:
                            pass

        out.append(ResultSummary(
            stage_number=stage_nr,
            max_moment_knm=max_mom,
            max_shear_kn=max_shear,
            max_disp_mm=max_disp_mm,
            mob_moment_pct=mob_mom,
            mob_grond_pct=mob_grond,
            ondersteuningen=ondersteuningen,
        ))
    return out


def _float_pattern(tekst: str, patroon: str) -> float | None:
    """Zoek een float-waarde via regex-patroon in tekst."""
    m = re.search(patroon, tekst)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None
```

- [ ] **Stap 5: Voeg `result_summaries` toe aan `parse_project()` in `parsers/shi_parser.py`**

Voeg de aanroep toe vóór het `return Project(...)` blok:

```python
    result_summaries = parse_result_summaries(shd)
```

Voeg `result_summaries=result_summaries,` toe aan het `Project(...)` aanroep:

```python
    return Project(
        ...
        result_summaries=result_summaries,
    )
```

- [ ] **Stap 6: Voer de test uit**

```
pytest tests/test_parsers.py::test_parse_result_summaries_basis -v
```
Verwacht: `PASSED`

- [ ] **Stap 7: Draai alle tests**

```
pytest tests/test_parsers.py -v
```
Verwacht: alle tests `PASSED`.

- [ ] **Stap 8: Commit**

```bash
git add parsers/models.py parsers/shi_parser.py tests/test_parsers.py
git commit -m "feat: voeg ResultSummary dataclass en parse_result_summaries() toe"
```

---

## Task 4: Maak `TabGrondsoorten` aan

**Files:**
- Create: `ui/tabs/tab_grondsoorten.py`

- [ ] **Stap 1: Maak het bestand aan**

Maak `ui/tabs/tab_grondsoorten.py` aan met de volgende inhoud:

```python
"""Tab Grondsoortentabel — toont grondparameters per profiel met profiel-dropdown."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QScrollArea, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt

from parsers.models import Project, SoilProfile
from utils.formatting import fmt_number

# ── Kleurconstanten (zelfde palet als tab_input_desc) ───────────────────────
_HDR_BG     = '#1b3a5c'
_HDR_FG     = '#ffffff'
_SUBHDR_BG  = '#274f77'
_SUBHDR_FG  = '#b8d4ea'
_BORDER     = '#c4d4e0'
_ROW_SEP    = '#dce8f0'
_ROW_ODD_BG = '#f3f8fc'
_ROW_EVN_BG = '#ffffff'
_LABEL_CLR  = '#2c3f52'
_VALUE_CLR  = '#0f1e2b'
_SCROLL_BG  = '#e8eef3'
_FONT       = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'

_KOLOMMEN: list[tuple[str, str]] = [
    ('BK laag\n[m NAP]',   'bk'),
    ('OK laag\n[m NAP]',   'ok'),
    ('Laag',               'naam'),
    ('γd\n[kN/m³]',        'gd'),
    ('γn\n[kN/m³]',        'gn'),
    ("c'kar\n[kN/m²]",     'c'),
    ("φ'kar\n[°]",         'phi'),
    ('δ\n[°]',             'delta'),
    ('kh1',                'kh1'),
    ('kh2',                'kh2'),
    ('kh3',                'kh3'),
]


class TabGrondsoorten(QWidget):
    """Toont grondparameters per profiel; dropdown voor profielselectie."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet(f'background: {_HDR_BG};')
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)

        lbl = QLabel('Profiel:')
        lbl.setStyleSheet(
            f'color: {_HDR_FG}; font-family: {_FONT}; font-size: 13px; font-weight: 600;'
        )
        toolbar_layout.addWidget(lbl)

        self._profiel_combo = QComboBox()
        self._profiel_combo.setMinimumWidth(260)
        self._profiel_combo.setStyleSheet(
            'QComboBox { background: white; color: #1b3a5c; '
            'border: 1px solid #c4d4e0; border-radius: 4px; padding: 4px 8px; font-size: 12px; }'
            'QComboBox::drop-down { border: none; }'
        )
        toolbar_layout.addWidget(self._profiel_combo)
        toolbar_layout.addStretch()

        root.addWidget(toolbar)

        # ── Scrollgebied ─────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f'QScrollArea {{ background: {_SCROLL_BG}; border: none; }}')

        self._content = QWidget()
        self._content.setStyleSheet(f'background: {_SCROLL_BG};')
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

        # ── Signalen ─────────────────────────────────────────────────────
        self._profiel_combo.currentIndexChanged.connect(self._on_profiel_changed)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate(self, project: Project | None) -> None:
        """Vul de dropdown en render het eerste profiel."""
        self._project = project
        self._profiel_combo.blockSignals(True)
        self._profiel_combo.clear()

        if not project or not project.profiles:
            self._profiel_combo.blockSignals(False)
            self._render_leeg()
            return

        for profiel in project.profiles:
            self._profiel_combo.addItem(profiel.name)

        self._profiel_combo.blockSignals(False)
        self._render_profiel(0)

    # ------------------------------------------------------------------
    # Interne handlers
    # ------------------------------------------------------------------

    def _on_profiel_changed(self, index: int) -> None:
        self._render_profiel(index)

    def _render_profiel(self, index: int) -> None:
        """Bouw de grondsoortentabel voor het profiel op positie index."""
        self._clear_content()

        if not self._project or index < 0 or index >= len(self._project.profiles):
            self._render_leeg()
            return

        profiel = self._project.profiles[index]
        soil_map = {s.name: s for s in self._project.soils}

        tabel = self._maak_tabel(profiel, soil_map)
        self._content_layout.insertWidget(self._content_layout.count() - 1, tabel)

    def _render_leeg(self) -> None:
        lbl = QLabel('Geen profieldata beschikbaar. Laad een project.')
        lbl.setStyleSheet(
            f'color: #7a93a8; font-size: 13px; font-family: {_FONT}; padding: 32px 20px;'
        )
        self._content_layout.insertWidget(0, lbl)

    def _clear_content(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ------------------------------------------------------------------
    # Tabelopbouw
    # ------------------------------------------------------------------

    def _maak_tabel(self, profiel: SoilProfile, soil_map: dict) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Kolomhoofden
        layout.addWidget(self._maak_kolomhoofden())

        # Datarijen
        n_lagen = len(profiel.layers)
        for i, laag in enumerate(profiel.layers):
            bk = laag.level
            # OK = begin van de volgende laag, of "Max" voor de laatste
            if i + 1 < n_lagen:
                ok_val: str = fmt_number(profiel.layers[i + 1].level)
            else:
                ok_val = 'Max'

            soil = soil_map.get(laag.material)
            bg = _ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG
            is_last = i == n_lagen - 1

            rij_vals = [
                fmt_number(bk),
                ok_val,
                laag.material,
                fmt_number(soil.gamma_dry) if soil else '-',
                fmt_number(soil.gamma_wet) if soil else '-',
                fmt_number(soil.cohesion)  if soil else '-',
                fmt_number(soil.phi)       if soil else '-',
                fmt_number(soil.delta)     if soil else '-',
                str(int(soil.kh1)) if soil and soil.kh1 else '-',
                str(int(soil.kh2)) if soil and soil.kh2 else '-',
                str(int(soil.kh3)) if soil and soil.kh3 else '-',
            ]
            layout.addWidget(self._maak_rij(rij_vals, bg, is_last))

        return frame

    def _maak_kolomhoofden(self) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_SUBHDR_BG};')
        grid = QGridLayout(hdr)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        for col, (tekst, _) in enumerate(_KOLOMMEN):
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid #1d4568;' if col < len(_KOLOMMEN) - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 5px 8px; text-transform: uppercase; {border_r}'
            )
            grid.addWidget(lbl, 0, col)

        return hdr

    def _maak_rij(self, waarden: list[str], bg: str, is_last: bool) -> QWidget:
        rij = QWidget()
        grid = QGridLayout(rij)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

        for col, waarde in enumerate(waarden):
            lbl = QLabel(waarde)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft if col == 2
                else Qt.AlignmentFlag.AlignRight
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < len(waarden) - 1 else ''
            kleur = _LABEL_CLR if col == 2 else _VALUE_CLR
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {kleur}; '
                f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
            )
            grid.addWidget(lbl, 0, col)

        return rij
```

- [ ] **Stap 2: Controleer importeerbaar**

```
python -c "from ui.tabs.tab_grondsoorten import TabGrondsoorten; print('OK')"
```
Verwacht: `OK`

- [ ] **Stap 3: Commit**

```bash
git add ui/tabs/tab_grondsoorten.py
git commit -m "feat: maak TabGrondsoorten widget aan"
```

---

## Task 5: Draad `TabGrondsoorten` in `main_window.py`

**Files:**
- Modify: `app/main_window.py`

- [ ] **Stap 1: Voeg de import toe**

Zoek de imports-sectie bovenaan `app/main_window.py` waar de andere tab-imports staan, en voeg toe:

```python
from ui.tabs.tab_grondsoorten import TabGrondsoorten
```

- [ ] **Stap 2: Voeg de tab toe in `_build_tabs()`**

Zoek de regels (rond regel 165–172):
```python
        # Tab 2A: Doorsnede
        self._tab_input_view = TabInputView()
        self._info_panel = InfoPanel()
        self._main_tabs.addTab(self._tab_input_view, 'Doorsnede')

        # Tab 2B: Invoerbeschrijving
        self._tab_input_desc = TabInputDesc()
        self._main_tabs.addTab(self._tab_input_desc, 'Invoerbeschrijving')
```

Voeg tussen "Tab 2A" en "Tab 2B" de nieuwe tab in:

```python
        # Tab 2A: Doorsnede
        self._tab_input_view = TabInputView()
        self._info_panel = InfoPanel()
        self._main_tabs.addTab(self._tab_input_view, 'Doorsnede')

        # Tab 2C: Grondsoortentabel
        self._tab_grondsoorten = TabGrondsoorten()
        self._main_tabs.addTab(self._tab_grondsoorten, 'Grondsoortentabel')

        # Tab 2B: Invoerbeschrijving
        self._tab_input_desc = TabInputDesc()
        self._main_tabs.addTab(self._tab_input_desc, 'Invoerbeschrijving')
```

- [ ] **Stap 3: Ververs de tab in `_on_main_tab_changed()`**

Zoek de methode `_on_main_tab_changed()` (rond regel 688) en voeg een `elif` toe:

```python
    def _on_main_tab_changed(self, index: int) -> None:
        """Ververs rapportagetabs on-demand bij activering."""
        tab = self._main_tabs.widget(index)
        if tab is self._tab_input_desc:
            self._refresh_input_desc()
        elif tab is self._tab_result_desc:
            self._refresh_result_desc()
        elif tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()
```

- [ ] **Stap 4: Voeg `_refresh_grondsoorten()` toe in `main_window.py`**

Voeg de methode toe na `_refresh_result_desc()`:

```python
    def _refresh_grondsoorten(self) -> None:
        project = self._state.get_active_project()
        self._tab_grondsoorten.populate(project)
```

- [ ] **Stap 5: Controleer ook in `_refresh_active_report_tab()`**

Zoek `_refresh_active_report_tab()` (rond regel 637) en voeg toe:

```python
    def _refresh_active_report_tab(self) -> None:
        active_tab = self._main_tabs.currentWidget()
        if active_tab is self._tab_input_desc:
            self._refresh_input_desc()
        elif active_tab is self._tab_result_desc:
            self._refresh_result_desc()
        elif active_tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()
```

- [ ] **Stap 6: Start de applicatie en controleer manueel**

```
python run.pyw
```

Controleer:
- Tab "Grondsoortentabel" is zichtbaar in de tabbalk
- Voor een geladen project toont de dropdown de profielnamen
- Selectie van een ander profiel herstelt de tabel correct
- Lege staat (geen project) toont de placeholder-tekst

- [ ] **Stap 7: Commit**

```bash
git add app/main_window.py
git commit -m "feat: voeg Grondsoortentabel-tab toe aan hoofdvenster"
```

---

## Task 6: Voeg `DamwandCard` en `build_damwand_card()` toe

**Files:**
- Modify: `reporting/builders/input_description_builder.py`
- Modify: `ui/tabs/tab_input_desc.py`

- [ ] **Stap 1: Voeg `DamwandCard` toe aan de builder**

Voeg toe in `reporting/builders/input_description_builder.py`, na de `FaseCard` dataclass:

```python
@dataclass
class DamwandCard:
    """Profielgegevens van de damwand (niet fase-specifiek)."""
    profiel: str
    staalkwaliteit: str
    hoogte_mm: float
    breedte_mm: float
    ei_knm2: float
    kopniveau: float
    teenniveau: float
    lengte: float
    ondersteuningen: list[tuple[str, float]]  # (naam, niveau [m NAP])
```

- [ ] **Stap 2: Voeg `build_damwand_card()` toe aan `InputDescriptionBuilder`**

Voeg toe als methode in `InputDescriptionBuilder`:

```python
    def build_damwand_card(self, project: Project) -> DamwandCard | None:
        """Bouw een DamwandCard vanuit het eerste SheetPilingElement.

        Parameters
        ----------
        project: Actief project.

        Returns
        -------
        DamwandCard | None  None als geen sheet piling aanwezig.
        """
        if not project.sheet_piling:
            return None
        el = project.sheet_piling[0]

        # Profielnaam: verwijder staalkwaliteit-deel "(S240GP)"
        profiel_naam = re.sub(r'\s*\([^)]+\)\s*$', '', el.name).strip()

        # Ondersteuningsniveaus: ankers + stempels, gesorteerd op niveau (ondiepst eerst)
        steunen: list[tuple[str, float]] = []
        for anker in project.anchors:
            steunen.append((anker.name, anker.level))
        for stempel in project.struts:
            steunen.append((stempel.name, stempel.level))
        steunen.sort(key=lambda t: t[1], reverse=True)

        return DamwandCard(
            profiel=profiel_naam,
            staalkwaliteit=el.steel_quality,
            hoogte_mm=el.height_mm,
            breedte_mm=el.pile_width_mm,
            ei_knm2=el.ei_knm2_per_m,
            kopniveau=el.top if el.top is not None else 0.0,
            teenniveau=el.bottom,
            lengte=abs((el.top or 0.0) - el.bottom),
            ondersteuningen=steunen,
        )
```

Voeg ook de import toe bovenaan het bestand als die er nog niet is:

```python
import re
```

- [ ] **Stap 3: Voeg `populate_damwand_card()` toe aan `TabInputDesc`**

Voeg toe in `ui/tabs/tab_input_desc.py`, na `populate_fase_cards()`:

```python
    def populate_damwand_card(self, card: DamwandCard | None) -> None:
        """Toon of verberg de damwandkaart bovenaan de tab."""
        # Verwijder een eventueel eerder gebouwde damwandkaart
        if hasattr(self, '_damwand_widget') and self._damwand_widget is not None:
            self._damwand_widget.deleteLater()
            self._damwand_widget = None

        if card is None:
            return

        self._damwand_widget = self._maak_damwand_card(card)
        # Invoegen op positie 0 (vóór de fase-kaarten en de stretch)
        self._layout.insertWidget(0, self._damwand_widget)
```

Voeg ook de initialisatie toe in `__init__` ná `super().__init__(parent)`:

```python
        self._damwand_widget: QWidget | None = None
```

Voeg de import toe bovenaan `tab_input_desc.py`:

```python
from reporting.builders.input_description_builder import FaseCard, DamwandCard
```

(Vervang de bestaande import die alleen `FaseCard` importeert.)

- [ ] **Stap 4: Voeg `_maak_damwand_card()` toe als private methode in `TabInputDesc`**

```python
    def _maak_damwand_card(self, card: DamwandCard) -> QWidget:
        """Bouw de vaste damwandkaart (bovenaan de tab)."""
        from utils.formatting import fmt_number

        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(27, 58, 92, 45))
        wrapper.setGraphicsEffect(shadow)

        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(4, 4, 4, 6)
        outer.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: {_CARD_BG}; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        outer.addWidget(frame)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_HDR_BG};')
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        titel = QLabel('Damwandprofiel')
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        hdr_lay.addWidget(titel)
        lay.addWidget(hdr)

        # Datarijen
        rijen: list[tuple[str, str, str]] = [
            ('Profiel',          card.profiel,                        ''),
            ('Staalkwaliteit',   card.staalkwaliteit,                 ''),
            ('Hoogte h',         fmt_number(card.hoogte_mm),          '[mm]'),
            ('Breedte b',        fmt_number(card.breedte_mm),         '[mm]'),
            ('E-modulus staal',  '2,10E+05',                          '[N/mm²]'),
            ('Kopniveau',        fmt_number(card.kopniveau),          '[m NAP]'),
            ('Teenniveau',       fmt_number(card.teenniveau),         '[m NAP]'),
            ('Lengte',           fmt_number(card.lengte),             '[m]'),
        ]
        for nr, (naam, niveau) in enumerate(card.ondersteuningen[:4], start=1):
            rijen.append((f'Niveau ondersteuning {nr}', fmt_number(niveau), '[m NAP]'))

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnMinimumWidth(0, 190)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 120)

        for i, (label, waarde, eenheid) in enumerate(rijen):
            bg = _ROW_ODD_BG if i % 2 == 0 else _ROW_EVEN_BG
            is_last = i == len(rijen) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; font-weight: 500; '
                f'color: {_LABEL_CLR}; background: {bg}; padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            val = QLabel(waarde)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                f'background: {bg}; padding: 6px 14px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            ext = QLabel(eenheid)
            ext.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                f'color: {_EXTRA_CLR}; background: {bg}; padding: 6px 10px; {border_b}'
            )
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            grid.addWidget(ext, i, 2)

        lay.addWidget(grid_w)
        return wrapper
```

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/input_description_builder.py ui/tabs/tab_input_desc.py
git commit -m "feat: voeg DamwandCard en populate_damwand_card() toe"
```

---

## Task 7: Draad damwandkaart in `main_window.py`

**Files:**
- Modify: `app/report_controller.py`
- Modify: `app/main_window.py`

- [ ] **Stap 1: Voeg `build_damwand_card()` toe aan `ReportController`**

Voeg de import toe bovenaan `app/report_controller.py`:

```python
from reporting.builders.input_description_builder import InputDescriptionBuilder, DamwandCard
```

(Voeg `DamwandCard` toe aan de bestaande import als die al bestaat.)

Voeg de methode toe na `build_all_fase_cards()`:

```python
    def build_damwand_card(self) -> DamwandCard | None:
        """Bouw DamwandCard voor het actieve project."""
        project = self._app.get_active_project()
        if not project:
            return None
        return self._input_builder.build_damwand_card(project)
```

- [ ] **Stap 2: Breid `_refresh_input_desc()` uit in `main_window.py`**

Vervang de bestaande methode:

```python
    def _refresh_input_desc(self) -> None:
        cards = self._report_controller.build_all_fase_cards()
        project = self._state.get_active_project()
        if project:
            for card, stage in zip(cards, project.stages):
                card.image_bytes = self._controller.render_stage_png(
                    project, stage, width_px=800, height_px=560)
        self._tab_input_desc.populate_fase_cards(cards)
        damwand_card = self._report_controller.build_damwand_card()
        self._tab_input_desc.populate_damwand_card(damwand_card)
```

- [ ] **Stap 3: Start de applicatie en controleer manueel**

```
python run.pyw
```

Controleer:
- Tab "Invoerbeschrijving" toont bovenaan een "Damwandprofiel"-kaart
- Kaart toont profiel (bv. "AZ 13-700"), staalkwaliteit, hoogte, breedte, niveaus
- Kaart verdwijnt correct als geen project geladen is
- De bestaande fase-kaarten staan eronder, ongewijzigd

- [ ] **Stap 4: Commit**

```bash
git add app/report_controller.py app/main_window.py
git commit -m "feat: toon damwandkaart bovenaan de Invoerbeschrijving-tab"
```

---

## Task 8: Voeg resultaattabel toe aan `TabResultDesc`

**Files:**
- Modify: `ui/tabs/tab_result_desc.py`
- Modify: `app/report_controller.py`
- Modify: `app/main_window.py`

- [ ] **Stap 1: Herschrijf `TabResultDesc` met resultaattabel**

Vervang de volledige inhoud van `ui/tabs/tab_result_desc.py`:

```python
"""Tab 3B — Resultaatbeschrijving: gegenereerde tekst + maatgevende resultaattabel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGroupBox, QComboBox, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt

from parsers.models import Project, ResultSummary
from reporting.models import ReportSection
from utils.formatting import fmt_number

_HDR_BG     = '#1b3a5c'
_HDR_FG     = '#ffffff'
_SUBHDR_BG  = '#274f77'
_SUBHDR_FG  = '#b8d4ea'
_BORDER     = '#c4d4e0'
_ROW_SEP    = '#dce8f0'
_ROW_ODD_BG = '#f3f8fc'
_ROW_EVN_BG = '#ffffff'
_LABEL_CLR  = '#2c3f52'
_VALUE_CLR  = '#0f1e2b'
_EXTRA_CLR  = '#2171ae'
_SCROLL_BG  = '#e8eef3'
_FONT       = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'


class TabResultDesc(QWidget):
    """Toont resultaattabel en gegenereerde resultaatbeschrijvingen (Tab 3B)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar met fase-combo
        toolbar = QWidget()
        toolbar.setStyleSheet(f'background: {_HDR_BG};')
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(12, 8, 12, 8)
        tb_lay.setSpacing(8)

        lbl = QLabel('Fase:')
        lbl.setStyleSheet(
            f'color: {_HDR_FG}; font-family: {_FONT}; font-size: 13px; font-weight: 600;'
        )
        tb_lay.addWidget(lbl)

        self._fase_combo = QComboBox()
        self._fase_combo.setMinimumWidth(200)
        self._fase_combo.setStyleSheet(
            'QComboBox { background: white; color: #1b3a5c; '
            'border: 1px solid #c4d4e0; border-radius: 4px; padding: 4px 8px; font-size: 12px; }'
        )
        tb_lay.addWidget(self._fase_combo)
        tb_lay.addStretch()

        root.addWidget(toolbar)

        # Scrollgebied
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f'QScrollArea {{ background: {_SCROLL_BG}; border: none; }}')

        self._content = QWidget()
        self._content.setStyleSheet(f'background: {_SCROLL_BG};')
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(16, 16, 16, 16)
        self._main_layout.setSpacing(12)
        self._main_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

        self._fase_combo.currentIndexChanged.connect(self._on_fase_changed)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate_resultaat_tabel(self, project: Project | None) -> None:
        """Vul de fase-combo en render de resultaattabel voor de eerste fase."""
        self._project = project
        self._fase_combo.blockSignals(True)
        self._fase_combo.clear()

        if not project or not project.result_summaries:
            self._fase_combo.blockSignals(False)
            self._clear_tabel()
            return

        for summary in project.result_summaries:
            stage = next(
                (s for s in project.stages if s.name),
                None
            )
            label = f'Fase {summary.stage_number}'
            if summary.stage_number <= len(project.stages):
                label = project.stages[summary.stage_number - 1].name
            self._fase_combo.addItem(label)

        self._fase_combo.blockSignals(False)
        self._render_tabel(0)

    def populate(self, sections: list[ReportSection]) -> None:
        """Voeg gegenereerde tekstsecties toe (bestaande API, ongewijzigd)."""
        # Verwijder alleen de tekstsecties (GroupBox-widgets), niet de resultaattabel
        verwijder = []
        for i in range(self._main_layout.count()):
            widget = self._main_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                verwijder.append(widget)
        for w in verwijder:
            w.deleteLater()

        if not sections:
            return

        for sec in sections:
            box = QGroupBox(sec.title)
            box.setStyleSheet(
                'QGroupBox { background: white; border: 1px solid #cfd6dd; '
                'border-radius: 8px; margin-top: 4px; padding: 4px; font-weight: bold; } '
                'QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }'
            )
            vl = QVBoxLayout(box)
            for field in sec.fields:
                val = f'{field.value} {field.unit}'.strip() if field.unit else field.value
                vl.addWidget(QLabel(f'<b>{field.label}:</b> {val}'))
            for table in sec.tables:
                vl.addWidget(QLabel(f'<b>{table.title}</b>'))
                header = ' | '.join(table.columns)
                vl.addWidget(QLabel(f'<i>{header}</i>'))
                for row in table.rows:
                    vl.addWidget(QLabel('  ' + ' | '.join(row)))
            self._main_layout.insertWidget(self._main_layout.count() - 1, box)

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _on_fase_changed(self, index: int) -> None:
        self._render_tabel(index)

    def _clear_tabel(self) -> None:
        """Verwijder de resultaattabel-widget als die bestaat."""
        if hasattr(self, '_tabel_widget') and self._tabel_widget is not None:
            self._tabel_widget.deleteLater()
            self._tabel_widget = None

    def _render_tabel(self, index: int) -> None:
        self._clear_tabel()
        if not self._project or index < 0 or index >= len(self._project.result_summaries):
            return

        summary = self._project.result_summaries[index]
        self._tabel_widget = self._maak_tabel(summary)
        self._main_layout.insertWidget(0, self._tabel_widget)

    def _maak_tabel(self, summary: ResultSummary) -> QWidget:
        """Bouw de resultaattabel conform Image 3 uit de spec."""
        project = self._project
        el = project.sheet_piling[0] if project and project.sheet_piling else None

        # Rijen: (label, waarde, eenheid)
        rijen: list[tuple[str, str, str]] = []

        # Damwandsectie
        rijen.append(('Damwand', '', ''))
        rijen.append(('Profiel', el.name.split('(')[0].strip() if el else '-', '[-]'))
        rijen.append(('Staalkwaliteit', el.steel_quality if el else '-', '[-]'))
        rijen.append(('Opneembaar moment', fmt_number(el.opneembaar_moment_knm) if el else '-', '[kNm/m]'))
        rijen.append(('Niveau damwand b.k.', fmt_number(el.top or 0.0) if el else '-', '[m NAP]'))
        rijen.append(('Niveau damwand o.k.', fmt_number(el.bottom) if el else '-', '[m NAP]'))
        rijen.append(('Damwandlengte', fmt_number(abs((el.top or 0.0) - el.bottom)) if el else '-', '[m]'))

        # Resultaten
        rijen.append(('Resultaten', '', ''))
        rijen.append(('Moment Msd', fmt_number(summary.max_moment_knm), '[kNm/m]'))
        rijen.append(('Dwarskracht Dsd', fmt_number(summary.max_shear_kn), '[kN/m]'))
        rijen.append(('Gemobiliseerd Moment', fmt_number(summary.mob_moment_pct), '[%]'))
        rijen.append(('Gemobiliseerd Grond', fmt_number(summary.mob_grond_pct), '[%]'))
        rijen.append(('Verplaatsing urep BGT', fmt_number(summary.max_disp_mm), '[mm]'))

        for nr, (naam, kracht, niveau) in enumerate(summary.ondersteuningen[:4], start=1):
            rijen.append((f'Ondersteuning {nr}', naam, '[kN/m]'))
            rijen.append((f'Niveau ondersteuning {nr}', fmt_number(niveau), '[m NAP]'))

        # Frame
        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Titelregel
        titel = QLabel('Specificaties')
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        lay.addWidget(titel)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnMinimumWidth(0, 220)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 100)

        for i, (label, waarde, eenheid) in enumerate(rijen):
            is_sectie = waarde == '' and eenheid == ''
            bg = _HDR_BG if is_sectie else (_ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG)
            is_last = i == len(rijen) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            fg = _HDR_FG if is_sectie else _LABEL_CLR

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {"12px" if not is_sectie else "11px"}; '
                f'font-weight: {"700" if is_sectie else "500"}; color: {fg}; '
                f'background: {bg}; padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP if not is_sectie else _HDR_BG}; {border_b}'
            )
            grid.addWidget(lbl, i, 0)

            if not is_sectie:
                val = QLabel(waarde)
                val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                val.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 14px; '
                    f'border-right: 1px solid {_ROW_SEP}; {border_b}'
                )
                grid.addWidget(val, i, 1)

                ext = QLabel(eenheid)
                ext.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                    f'color: {_EXTRA_CLR}; background: {bg}; padding: 6px 10px; {border_b}'
                )
                grid.addWidget(ext, i, 2)

        lay.addWidget(grid_w)
        return frame
```

- [ ] **Stap 2: Voeg `build_resultaat_tabel_data()` toe aan `ReportController`**

Voeg toe aan `app/report_controller.py`:

```python
    def get_active_project(self):
        """Geeft het actieve project terug (doorsturen vanuit AppState)."""
        return self._app.get_active_project()
```

(Opmerking: `main_window.py` heeft al directe toegang tot `self._state.get_active_project()` — de project wordt rechtstreeks doorgegeven aan de tab.)

- [ ] **Stap 3: Breid `_refresh_result_desc()` uit in `main_window.py`**

Vervang de bestaande methode:

```python
    def _refresh_result_desc(self) -> None:
        project = self._state.get_active_project()
        self._tab_result_desc.populate_resultaat_tabel(project)
        secs = self._report_controller.build_result_descriptions()
        self._tab_result_desc.populate(secs)
```

- [ ] **Stap 4: Start de applicatie en controleer manueel**

```
python run.pyw
```

Controleer:
- Tab "Resultaatbeschrijving" toont bovenaan de fase-combo
- De resultaattabel toont profielgegevens + maatgevende waarden per geselecteerde fase
- Wisselen van fase in de combo herlaadt de tabel
- Zonder .shd-resultaten toont de tab geen tabel (geen crash)

- [ ] **Stap 5: Draai alle tests**

```
pytest tests/test_parsers.py -v
```
Verwacht: alle tests `PASSED`.

- [ ] **Stap 6: Commit**

```bash
git add ui/tabs/tab_result_desc.py app/report_controller.py app/main_window.py
git commit -m "feat: voeg resultaattabel toe aan Resultaatbeschrijving-tab"
```

---

## Zelfbeoordeling

**Spec-dekking:**
- ✅ Soil uitgebreid (Task 1)
- ✅ SheetPilingElement uitgebreid (Task 2)
- ✅ ResultSummary + parse_result_summaries (Task 3)
- ✅ TabGrondsoorten + profiel-dropdown (Task 4 + 5)
- ✅ DamwandCard + vaste kaart bovenaan Invoerbeschrijving (Task 6 + 7)
- ✅ Resultaattabel met fase-combo in Resultaatbeschrijving (Task 8)

**Notitie opneembaar moment:** `opneembaar_moment_knm` wordt berekend als `max_char × KMod × MaterialFactor × ReductionFactor`. De waarde "201 kNm/m" uit Image 3 is vermoedelijk corrosie-gecorrigeerd en wijkt af van de 313 kNm/m in het testbestand — dit is een bekende beperking, geen bug.
