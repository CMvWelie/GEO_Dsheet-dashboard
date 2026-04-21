# TabVerticaalEvenwicht Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voeg subtabblad "Verticaal evenwicht" toe aan "Aanvullende berekeningen" voor opbarstcontrole conform NEN 9997-1:2016 art. 10.2(a).

**Architecture:** Pure berekeningsfuncties + data-extractie uit Project-model + PyQt6 widget. Exact hetzelfde patroon als `TabHydraulischeGrondbreuk`. Alle Qt-vrije logica is testbaar zonder display.

**Tech Stack:** Python 3.10+, PyQt6, `parsers.models` (Project, Surface, SoilProfile, SoilLayer, Soil, WaterLevel, Stage), `utils.formatting.fmt_number`

---

## Bestandsoverzicht

| Actie | Pad | Verantwoordelijkheid |
|---|---|---|
| Create | `ui/tabs/tab_verticaal_evenwicht.py` | Dataclasses, pure functies, QWidget |
| Create | `tests/test_verticaal_evenwicht.py` | Unit tests voor alle pure functies |
| Modify | `ui/tabs/tab_aanvullende_berekeningen.py` | Importeer + voeg subtab toe |

---

## Task 1: Berekeningsfuncties + tests

**Files:**
- Create: `ui/tabs/tab_verticaal_evenwicht.py` (skeleton + pure functies)
- Create: `tests/test_verticaal_evenwicht.py`

- [ ] **Stap 1.1 — Schrijf het skelet van `tab_verticaal_evenwicht.py`**

Maak het bestand aan met alleen imports en de twee pure functies als stub:

```python
"""Subtab Verticaal evenwicht — opbarstcontrole conform NEN 9997-1:2016."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from parsers.models import Project, Surface, SoilProfile, Stage


@dataclass
class TaludGeometrie:
    """Geometrie van één talud naast de bouwput."""
    maaiveld_niveau: float
    helling_h_per_v: float


@dataclass
class AutoWaardenVE:
    """Waarden die automatisch uit een Project worden ingevuld."""
    ontgravingsniveau: float | None
    breedte_bouwputbodem: float | None
    stijghoogte: float | None
    waterpeil_bouwput: float | None
    grondlagen: list[tuple[str, float, float, float, float]] = field(default_factory=list)
    # (naam, bovenkant_m_NAP, onderkant_m_NAP, gamma_dr_kNm3, gamma_nat_kNm3)
    talud_links: TaludGeometrie | None = None
    talud_rechts: TaludGeometrie | None = None


def bereken_taludinvloed(d1: float, a: float, b: float, d2: float) -> float:
    """Bereken de f-factor voor taludinvloed conform NEN 9997-1:2016 art. 10.2(a).

    Parameters
    ----------
    d1: Hoogte van grond naast sleuf (maaiveld - ontgravingsniveau) [m].
    a:  Horizontale afstand van sleufrand tot teen talud (= d1 * h/v) [m].
    b:  Halve breedte bouwputbodem [m].
    d2: Diepte van ontgravingsniveau tot evenwichtsniveau [m].

    Returns
    -------
    float
        Dimensieloze f-factor [-].
    """
    raise NotImplementedError


def bereken_verticaal_evenwicht(
    lagen: list[tuple[str, float, float, float, float]],
    ontgravingsniveau: float,
    waterpeil_bouwput: float,
    stijghoogte: float,
    evenwichtsniveau: float,
    materiaalfactor: float,
    watergewicht: float,
) -> tuple[float, float, float]:
    """Bereken de verticaal-evenwichtcontrole (opbarsten).

    Parameters
    ----------
    lagen:              Lijst (naam, bk, ok, γ_dr, γ_nat) — volledig profiel.
    ontgravingsniveau:  Bouwputniveau [m NAP].
    waterpeil_bouwput:  Freatisch peil in bouwput [m NAP].
    stijghoogte:        Artesiaanse stijghoogte w.v.p. [m NAP].
    evenwichtsniveau:   Onderkant waterremmende laag [m NAP].
    materiaalfactor:    γG;stb [-].
    watergewicht:       γ_w [kN/m³].

    Returns
    -------
    tuple[float, float, float]
        (Gstb_d [kN/m²], Vdst_d [kN/m²], UC [-]).
        UC is math.inf als Vdst_d nul is.
    """
    raise NotImplementedError
```

- [ ] **Stap 1.2 — Schrijf de falende tests voor `bereken_taludinvloed`**

Maak `tests/test_verticaal_evenwicht.py` aan.
Importeer alleen wat in Task 1 beschikbaar is — de overige imports worden in stap 2.6 toegevoegd:

```python
"""Tests voor verticaal evenwicht berekeningslogica."""
from __future__ import annotations

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.tabs.tab_verticaal_evenwicht import (
    bereken_taludinvloed,
    bereken_verticaal_evenwicht,
)
from parsers.models import Project, FileBundle, Surface, WaterLevel, Soil, SoilProfile, SoilLayer, Stage


# ---------------------------------------------------------------------------
# bereken_taludinvloed
# ---------------------------------------------------------------------------

def test_taludinvloed_excel_waarden():
    """Rekenvoorbeeld uit Excel: d1=29, a=87, b=3.325, d2=9.5 → f≈0.0392."""
    f = bereken_taludinvloed(d1=29.0, a=87.0, b=3.325, d2=9.5)
    assert abs(f - 0.0392) < 0.001


def test_taludinvloed_nul_bij_geen_helling():
    """a=0 (vlak terrein) geeft f=0."""
    f = bereken_taludinvloed(d1=0.0, a=0.0, b=3.0, d2=9.0)
    assert f == 0.0


def test_taludinvloed_positief():
    """f is altijd ≥ 0."""
    f = bereken_taludinvloed(d1=5.0, a=15.0, b=3.0, d2=8.0)
    assert f >= 0.0
```

- [ ] **Stap 1.3 — Draai de tests en verifieer dat ze falen**

```
pytest tests/test_verticaal_evenwicht.py::test_taludinvloed_excel_waarden tests/test_verticaal_evenwicht.py::test_taludinvloed_nul_bij_geen_helling tests/test_verticaal_evenwicht.py::test_taludinvloed_positief -v
```

Verwacht: **FAIL** met `NotImplementedError`.

- [ ] **Stap 1.4 — Implementeer `bereken_taludinvloed`**

Vervang de stub in `tab_verticaal_evenwicht.py`:

```python
def bereken_taludinvloed(d1: float, a: float, b: float, d2: float) -> float:
    if a <= 0.0 or b <= 0.0 or d1 <= 0.0:
        return 0.0
    b_over_a = b / a
    return (2.0 / math.pi) * (
        (1.0 + b_over_a) * math.atan(d2 / (a + b))
        - b_over_a * math.atan(d2 / b)
    )
```

- [ ] **Stap 1.5 — Draai de tests en verifieer dat ze slagen**

```
pytest tests/test_verticaal_evenwicht.py::test_taludinvloed_excel_waarden tests/test_verticaal_evenwicht.py::test_taludinvloed_nul_bij_geen_helling tests/test_verticaal_evenwicht.py::test_taludinvloed_positief -v
```

Verwacht: **3 PASSED**.

- [ ] **Stap 1.6 — Schrijf de falende tests voor `bereken_verticaal_evenwicht`**

Voeg toe aan `tests/test_verticaal_evenwicht.py`:

```python
# ---------------------------------------------------------------------------
# bereken_verticaal_evenwicht
# ---------------------------------------------------------------------------

def test_verticaal_evenwicht_excel_waarden():
    """Rekenvoorbeeld uit Excel: Gstb≈107.69, Vdst=107.0, UC≈1.006."""
    lagen = [
        ('Klei siltig',  -4.0,  -6.5, 14.0, 14.0),
        ('Veen',         -6.5,  -9.8, 10.5, 10.5),
        ('Klei schoon',  -9.8, -12.6, 14.0, 14.0),
        ('Basisveen',   -12.6, -13.5, 12.0, 12.0),
    ]
    gstb, vdst, uc = bereken_verticaal_evenwicht(
        lagen=lagen,
        ontgravingsniveau=-4.0,
        waterpeil_bouwput=-4.0,
        stijghoogte=-2.8,
        evenwichtsniveau=-13.5,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert abs(gstb - 107.685) < 0.01
    assert abs(vdst - 107.0) < 0.01
    assert abs(uc - 1.0064) < 0.001


def test_verticaal_evenwicht_droog_nat_split():
    """Lagen boven waterpeil gebruiken gamma_dr, lagen eronder gamma_nat."""
    lagen = [('Zand', -2.0, -4.0, 18.0, 20.0)]
    gstb, _vdst, _uc = bereken_verticaal_evenwicht(
        lagen=lagen,
        ontgravingsniveau=-2.0,
        waterpeil_bouwput=-3.0,
        stijghoogte=0.0,
        evenwichtsniveau=-4.0,
        materiaalfactor=1.0,
        watergewicht=10.0,
    )
    # 1m droog (18 kN/m³) + 1m nat (20 kN/m³), materiaalfactor=1.0
    assert abs(gstb - 38.0) < 0.01


def test_verticaal_evenwicht_geen_waterdruk():
    """Stijghoogte gelijk aan evenwichtsniveau → Vdst=0, UC=inf."""
    lagen = [('Klei', -4.0, -10.0, 14.0, 14.0)]
    gstb, vdst, uc = bereken_verticaal_evenwicht(
        lagen=lagen,
        ontgravingsniveau=-4.0,
        waterpeil_bouwput=-4.0,
        stijghoogte=-10.0,
        evenwichtsniveau=-10.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert vdst == 0.0
    assert math.isinf(uc)


def test_verticaal_evenwicht_voldoet_niet():
    """UC < 1.0 als waterdruk groter is dan grondgewicht."""
    lagen = [('Klei', -4.0, -6.0, 10.0, 10.0)]
    _gstb, _vdst, uc = bereken_verticaal_evenwicht(
        lagen=lagen,
        ontgravingsniveau=-4.0,
        waterpeil_bouwput=-4.0,
        stijghoogte=0.0,
        evenwichtsniveau=-6.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert uc < 1.0
```

- [ ] **Stap 1.7 — Draai en verifieer FAIL**

```
pytest tests/test_verticaal_evenwicht.py -k "verticaal_evenwicht" -v
```

Verwacht: **FAIL** met `NotImplementedError`.

- [ ] **Stap 1.8 — Implementeer `bereken_verticaal_evenwicht`**

Vervang de stub en voeg ook `bereken_gewicht_talud` toe direct erna:

```python
def bereken_verticaal_evenwicht(
    lagen: list[tuple[str, float, float, float, float]],
    ontgravingsniveau: float,
    waterpeil_bouwput: float,
    stijghoogte: float,
    evenwichtsniveau: float,
    materiaalfactor: float,
    watergewicht: float,
) -> tuple[float, float, float]:
    gstb = 0.0
    for _naam, bk, ok, gamma_dr, gamma_nat in lagen:
        effectief_bk = min(bk, ontgravingsniveau)
        effectief_ok = max(ok, evenwichtsniveau)
        if effectief_bk <= effectief_ok:
            continue
        dikte_boven = max(0.0, effectief_bk - max(effectief_ok, waterpeil_bouwput))
        dikte_onder = max(0.0, min(effectief_bk, waterpeil_bouwput) - effectief_ok)
        gstb += (dikte_boven * gamma_dr + dikte_onder * gamma_nat) * materiaalfactor

    vdst = max(0.0, (stijghoogte - evenwichtsniveau) * watergewicht)
    uc = gstb / vdst if vdst > 0.0 else math.inf
    return gstb, vdst, uc


def bereken_gewicht_talud(
    lagen: list[tuple[str, float, float, float, float]],
    maaiveld_niveau: float,
    ontgravingsniveau: float,
) -> float:
    """Gewicht van grond naast de sleuf (van maaiveld tot ontgravingsniveau) [kN/m²].

    Parameters
    ----------
    lagen:              Volledig grondprofiel (naam, bk, ok, γ_dr, γ_nat).
    maaiveld_niveau:    Maaiveldniveau aan de taludzijde [m NAP].
    ontgravingsniveau:  Bouwputniveau [m NAP].

    Returns
    -------
    float
        Neerwaarste druk uit het talud [kN/m²].
    """
    gewicht = 0.0
    for _naam, bk, ok, gamma_dr, _gamma_nat in lagen:
        effectief_bk = min(bk, maaiveld_niveau)
        effectief_ok = max(ok, ontgravingsniveau)
        if effectief_bk <= effectief_ok:
            continue
        gewicht += (effectief_bk - effectief_ok) * gamma_dr
    return gewicht
```

- [ ] **Stap 1.9 — Draai en verifieer PASS**

```
pytest tests/test_verticaal_evenwicht.py -k "taludinvloed or verticaal_evenwicht" -v
```

Verwacht: **7 PASSED**.

- [ ] **Stap 1.10 — Commit**

```bash
git add ui/tabs/tab_verticaal_evenwicht.py tests/test_verticaal_evenwicht.py
git commit -m "feat: voeg berekeningsfuncties toe voor verticaal evenwicht"
```

---

## Task 2: Data-extractie uit Surface + Project

**Files:**
- Modify: `ui/tabs/tab_verticaal_evenwicht.py` (voeg extractiefuncties toe)
- Modify: `tests/test_verticaal_evenwicht.py` (voeg tests toe)

- [ ] **Stap 2.1 — Schrijf falende tests voor `_zoek_bodem_punten`**

Voeg toe aan `tests/test_verticaal_evenwicht.py`:

```python
# ---------------------------------------------------------------------------
# _zoek_bodem_punten
# ---------------------------------------------------------------------------

def _maak_surface(punten: list[tuple[float, float]]) -> Surface:
    return Surface(
        nr=1, name='test',
        points=[{'nr': i+1, 'x': x, 'y': y} for i, (x, y) in enumerate(punten)],
    )


def test_zoek_bodem_punten_symmetrisch():
    """Symmetrische bouwput: bodempunten op x=-3.325 en x=3.325, y=-4."""
    surf = _maak_surface([(-10.0, 0.0), (-3.325, -4.0), (3.325, -4.0), (10.0, 0.0)])
    x_l, x_r, min_y = _zoek_bodem_punten(surf)
    assert abs(x_l - (-3.325)) < 0.001
    assert abs(x_r - 3.325) < 0.001
    assert abs(min_y - (-4.0)) < 0.001


def test_zoek_bodem_punten_breedte():
    """Breedte = x_r - x_l."""
    surf = _maak_surface([(0.0, -4.0), (6.65, -4.0)])
    x_l, x_r, _y = _zoek_bodem_punten(surf)
    assert abs((x_r - x_l) - 6.65) < 0.001
```

- [ ] **Stap 2.2 — Schrijf falende tests voor `extraheer_talud_links` en `extraheer_talud_rechts`**

Voeg toe aan `tests/test_verticaal_evenwicht.py`:

```python
# ---------------------------------------------------------------------------
# extraheer_talud_links / rechts
# ---------------------------------------------------------------------------

def test_extraheer_talud_links_helling_1_op_3():
    """Links talud 1:3 (v:h): bouwput -4 m NAP, maaiveld 0 m NAP.
    Horizontale afstand = 4 * 3 = 12 m → helling_h_per_v = 3.0."""
    surf = _maak_surface([
        (-15.325, 0.0),   # top talud links
        (-3.325,  -4.0),  # linker sleufrand
        (3.325,   -4.0),  # rechter sleufrand
        (15.325,  0.0),   # top talud rechts
    ])
    talud = extraheer_talud_links(surf)
    assert talud is not None
    assert abs(talud.maaiveld_niveau - 0.0) < 0.01
    assert abs(talud.helling_h_per_v - 3.0) < 0.01


def test_extraheer_talud_rechts_helling_1_op_2():
    """Rechts talud 1:2 (v:h): bouwput -4, maaiveld 0.
    Horizontale afstand = 4 * 2 = 8 m → helling_h_per_v = 2.0."""
    surf = _maak_surface([
        (-15.0,  0.0),
        (-3.325, -4.0),
        (3.325,  -4.0),
        (11.325, 0.0),   # 3.325 + 8.0
    ])
    talud = extraheer_talud_rechts(surf)
    assert talud is not None
    assert abs(talud.maaiveld_niveau - 0.0) < 0.01
    assert abs(talud.helling_h_per_v - 2.0) < 0.01


def test_extraheer_talud_vlak_geeft_helling_nul():
    """Volledig vlak terrein → helling_h_per_v = 0."""
    surf = _maak_surface([(0.0, 0.0), (6.65, 0.0)])
    talud_l = extraheer_talud_links(surf)
    assert talud_l is not None
    assert talud_l.helling_h_per_v == 0.0
```

- [ ] **Stap 2.3 — Draai en verifieer FAIL**

```
pytest tests/test_verticaal_evenwicht.py -k "bodem_punten or talud_links or talud_rechts or talud_vlak" -v
```

Verwacht: **FAIL** met `ImportError` of `NotImplementedError`.

- [ ] **Stap 2.4 — Implementeer `_zoek_bodem_punten`, `extraheer_talud_links`, `extraheer_talud_rechts`**

Voeg toe aan `tab_verticaal_evenwicht.py` na de berekeningsfuncties:

```python
# ------------------------------------------------------------------
# Surface-extractie
# ------------------------------------------------------------------

def _zoek_bodem_punten(surface: Surface) -> tuple[float, float, float]:
    """Geeft (x_links, x_rechts, min_y) van de twee laagste Surface-punten.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel.

    Returns
    -------
    tuple[float, float, float]
        (x_links, x_rechts, ontgravingsniveau_m_NAP).
    """
    min_y = min(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_links = min(pt['x'] for pt in bodem)
    x_rechts = max(pt['x'] for pt in bodem)
    return x_links, x_rechts, min_y


def extraheer_talud_links(surface: Surface) -> TaludGeometrie:
    """Leid maaiveldniveau en helling af voor het linkse talud.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel (dekt volledige breedte).

    Returns
    -------
    TaludGeometrie
        Maaiveldniveau en helling_h_per_v (0.0 bij vlak terrein).
    """
    min_y = min(pt['y'] for pt in surface.points)
    maaiveld_niveau = max(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_links_bodem = min(pt['x'] for pt in bodem)
    links_punten = [pt for pt in surface.points if pt['x'] <= x_links_bodem]
    d1 = maaiveld_niveau - min_y
    if not links_punten or d1 <= 0.0:
        return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=0.0)
    x_top_links = min(pt['x'] for pt in links_punten)
    dx = x_links_bodem - x_top_links
    return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=dx / d1)


def extraheer_talud_rechts(surface: Surface) -> TaludGeometrie:
    """Leid maaiveldniveau en helling af voor het rechtse talud.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel (dekt volledige breedte).

    Returns
    -------
    TaludGeometrie
        Maaiveldniveau en helling_h_per_v (0.0 bij vlak terrein).
    """
    min_y = min(pt['y'] for pt in surface.points)
    maaiveld_niveau = max(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_rechts_bodem = max(pt['x'] for pt in bodem)
    rechts_punten = [pt for pt in surface.points if pt['x'] >= x_rechts_bodem]
    d1 = maaiveld_niveau - min_y
    if not rechts_punten or d1 <= 0.0:
        return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=0.0)
    x_top_rechts = max(pt['x'] for pt in rechts_punten)
    dx = x_top_rechts - x_rechts_bodem
    return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=dx / d1)
```

- [ ] **Stap 2.5 — Draai en verifieer PASS**

```
pytest tests/test_verticaal_evenwicht.py -k "bodem_punten or talud_links or talud_rechts or talud_vlak" -v
```

Verwacht: **5 PASSED**.

- [ ] **Stap 2.6 — Schrijf falende test voor `extraheer_auto_waarden_ve`**

Voeg eerst de ontbrekende imports toe bovenaan `tests/test_verticaal_evenwicht.py`
(na de bestaande imports):

```python
from ui.tabs.tab_verticaal_evenwicht import (
    bereken_gewicht_talud,
    extraheer_talud_links,
    extraheer_talud_rechts,
    extraheer_auto_waarden_ve,
    _zoek_bodem_punten,
    TaludGeometrie,
    AutoWaardenVE,
)
```

Voeg daarna de tests toe aan `tests/test_verticaal_evenwicht.py`:

```python
# ---------------------------------------------------------------------------
# extraheer_auto_waarden_ve
# ---------------------------------------------------------------------------

def _maak_project_ve() -> Project:
    """Minimaal testproject met surface, waterlevels, profiel en grondsoorten."""
    surf = Surface(nr=1, name='Maaiveld', points=[
        {'nr': 1, 'x': -15.325, 'y':  0.0},
        {'nr': 2, 'x':  -3.325, 'y': -4.0},
        {'nr': 3, 'x':   3.325, 'y': -4.0},
        {'nr': 4, 'x':  15.325, 'y':  0.0},
    ])
    klei = Soil(name='Klei', color='rgb(0,0,0)', color_int=None,
                gamma_dry=14.0, gamma_wet=14.0)
    profiel = SoilProfile(
        name='Links', normalized_name='links', occurrence=1, x=None, y=None,
        layers=[
            SoilLayer(nr=1, level=0.3,  wosp_top=0.0, wosp_bottom=0.0, material='Klei'),
            SoilLayer(nr=2, level=-6.5, wosp_top=0.0, wosp_bottom=0.0, material='Klei'),
        ],
    )
    stage = Stage(
        name='Fase 1',
        left_surface='Maaiveld', right_surface='Maaiveld',
        left_profile='Links',   right_profile='Links',
    )
    return Project(
        base_name='test', project_name='Test', file_bundle=FileBundle(),
        surfaces=[surf],
        waterlevels=[WaterLevel(name='Stijghoogte', level=-2.8)],
        soils=[klei],
        profiles=[profiel],
        stages=[stage],
    )


def test_extraheer_auto_waarden_ve_breedte_en_ontgraving():
    """Breedte = 6.65 m, ontgravingsniveau = -4.0 m NAP."""
    project = _maak_project_ve()
    auto = extraheer_auto_waarden_ve(project, 'Fase 1', 'links')
    assert abs(auto.breedte_bouwputbodem - 6.65) < 0.01
    assert abs(auto.ontgravingsniveau - (-4.0)) < 0.01


def test_extraheer_auto_waarden_ve_stijghoogte():
    """Stijghoogte = hoogste waterpeil."""
    project = _maak_project_ve()
    auto = extraheer_auto_waarden_ve(project, 'Fase 1', 'links')
    assert abs(auto.stijghoogte - (-2.8)) < 0.01


def test_extraheer_auto_waarden_ve_talud_helling():
    """Links talud: helling_h_per_v = (15.325 - 3.325) / 4.0 = 3.0."""
    project = _maak_project_ve()
    auto = extraheer_auto_waarden_ve(project, 'Fase 1', 'links')
    assert auto.talud_links is not None
    assert abs(auto.talud_links.helling_h_per_v - 3.0) < 0.01


def test_extraheer_auto_waarden_ve_grondlagen():
    """Grondlagen bevat minstens 1 laag met correcte naam."""
    project = _maak_project_ve()
    auto = extraheer_auto_waarden_ve(project, 'Fase 1', 'links')
    assert len(auto.grondlagen) >= 1
    naam, bk, ok, gdr, gnat = auto.grondlagen[0]
    assert naam == 'Klei'
    assert abs(gdr - 14.0) < 0.01
    assert abs(gnat - 14.0) < 0.01


def test_extraheer_auto_waarden_ve_onbekende_stage():
    """Onbekende stage-naam → ontgravingsniveau en breedte None."""
    project = _maak_project_ve()
    auto = extraheer_auto_waarden_ve(project, 'Onbekend', 'links')
    assert auto.ontgravingsniveau is None
    assert auto.breedte_bouwputbodem is None
```

- [ ] **Stap 2.7 — Draai en verifieer FAIL**

```
pytest tests/test_verticaal_evenwicht.py -k "auto_waarden" -v
```

Verwacht: **FAIL** met `ImportError`.

- [ ] **Stap 2.8 — Implementeer `extraheer_auto_waarden_ve`**

Voeg toe aan `tab_verticaal_evenwicht.py` na de surface-extractiefuncties:

```python
def extraheer_auto_waarden_ve(
    project: Project,
    stage_naam: str,
    profiel_zijde: str,
) -> AutoWaardenVE:
    """Extraheert auto-invulwaarden voor verticaal evenwicht uit een Project.

    Parameters
    ----------
    project:      Geparseerd D-Sheet project.
    stage_naam:   Naam van de te gebruiken rekenfase.
    profiel_zijde: 'links' of 'rechts' — welk grondprofiel als basis.

    Returns
    -------
    AutoWaardenVE
        Alle auto-waarden; velden zijn None als bron ontbreekt.
    """
    def _find_surface(naam: str) -> Surface | None:
        return next((s for s in project.surfaces if s.name == naam), None)

    stage = next((s for s in project.stages if s.name == stage_naam), None)

    stijghoogte = max((wl.level for wl in project.waterlevels), default=None)

    # Breedte en ontgravingsniveau uit left_surface
    surf_links_naam = stage.left_surface if stage else None
    surf_rechts_naam = stage.right_surface if stage else None
    surf_links = _find_surface(surf_links_naam) if surf_links_naam else None
    surf_rechts = _find_surface(surf_rechts_naam) if surf_rechts_naam else None

    ref_surf = surf_links or surf_rechts
    breedte = None
    ontgravingsniveau = None
    if ref_surf and ref_surf.points:
        x_l, x_r, min_y = _zoek_bodem_punten(ref_surf)
        breedte = abs(x_r - x_l)
        ontgravingsniveau = min_y

    talud_links = extraheer_talud_links(surf_links) if surf_links and surf_links.points else None
    talud_rechts = extraheer_talud_rechts(surf_rechts) if surf_rechts and surf_rechts.points else None

    # Grondprofiel
    profiel_naam = (
        (stage.left_profile if profiel_zijde == 'links' else stage.right_profile)
        if stage else None
    )
    profiel = next((p for p in project.profiles if p.name == profiel_naam), None)
    soil_map = {s.name: s for s in project.soils}
    grondlagen: list[tuple[str, float, float, float, float]] = []
    if profiel and profiel.layers:
        for i, laag in enumerate(profiel.layers):
            ok = (
                profiel.layers[i + 1].level
                if i + 1 < len(profiel.layers)
                else laag.level - 30.0
            )
            bodem = soil_map.get(laag.material)
            gamma_dr = bodem.gamma_dry if bodem else 0.0
            gamma_nat = bodem.gamma_wet if bodem else 0.0
            grondlagen.append((laag.material, laag.level, ok, gamma_dr, gamma_nat))

    return AutoWaardenVE(
        ontgravingsniveau=ontgravingsniveau,
        breedte_bouwputbodem=breedte,
        stijghoogte=stijghoogte,
        waterpeil_bouwput=stijghoogte,
        grondlagen=grondlagen,
        talud_links=talud_links,
        talud_rechts=talud_rechts,
    )
```

Voeg ook de ontbrekende import toe bovenaan het bestand (als die nog niet aanwezig is):

```python
from parsers.models import Project, Surface, SoilProfile, SoilLayer, Stage
```

- [ ] **Stap 2.9 — Draai alle tests en verifieer PASS**

```
pytest tests/test_verticaal_evenwicht.py -v
```

Verwacht: **alle tests PASSED**.

- [ ] **Stap 2.10 — Commit**

```bash
git add ui/tabs/tab_verticaal_evenwicht.py tests/test_verticaal_evenwicht.py
git commit -m "feat: voeg data-extractie toe voor verticaal evenwicht"
```

---

## Task 3: TabVerticaalEvenwicht UI-widget

**Files:**
- Modify: `ui/tabs/tab_verticaal_evenwicht.py` (voeg klasse toe onderaan)

Geen aparte unit tests voor de widget (PyQt6 vereist display). Functioneel testen in Task 4.

- [ ] **Stap 3.1 — Voeg PyQt6-imports en constanten toe bovenaan het bestand**

Voeg toe direct na de `from parsers.models` import:

```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QGroupBox, QGridLayout, QComboBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.formatting import fmt_number

_MATERIAALFACTOR_STANDAARD = 0.9
_WATERGEWICHT_STANDAARD = 10.0
```

- [ ] **Stap 3.2 — Voeg de klasse-definitie toe met `_build` en hulpmethoden**

Voeg toe onderaan `tab_verticaal_evenwicht.py`:

```python
class TabVerticaalEvenwicht(QWidget):
    """Subtab met verticaal-evenwichtcontrole (opbarsten, NEN 9997-1:2016)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._auto_waarden: AutoWaardenVE | None = None
        self._laatste_project_naam: str | None = None
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._bouw_instellingen_groep())
        layout.addWidget(self._bouw_invoer_groep())
        layout.addWidget(self._bouw_resultaat_groep())
        layout.addStretch()
        self._verbind_signalen()
        self._herbereken()

    def _bouw_instellingen_groep(self) -> QGroupBox:
        groep = QGroupBox('Projectinstellingen')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._combo_stage = QComboBox()
        self._combo_profiel = QComboBox()
        self._combo_profiel.addItems(['Links', 'Rechts'])
        self._combo_evenwicht = QComboBox()

        grid.addWidget(QLabel('Stage'), 0, 0)
        grid.addWidget(self._combo_stage, 0, 1)
        grid.addWidget(QLabel('Grondprofiel'), 1, 0)
        grid.addWidget(self._combo_profiel, 1, 1)
        grid.addWidget(QLabel('Evenwichtsniveau-laag (o.k.)'), 2, 0)
        grid.addWidget(self._combo_evenwicht, 2, 1)
        return groep

    def _bouw_invoer_groep(self) -> QGroupBox:
        groep = QGroupBox('Invoer')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._spin_ontgraving      = self._maak_spin(-50.0, 50.0, 2)
        self._spin_waterpeil       = self._maak_spin(-50.0, 50.0, 2)
        self._spin_stijghoogte     = self._maak_spin(-50.0, 50.0, 2)
        self._spin_materiaalfactor = self._maak_spin(0.0, 2.0, 2)
        self._spin_watergewicht    = self._maak_spin(0.0, 20.0, 1)
        self._spin_materiaalfactor.setValue(_MATERIAALFACTOR_STANDAARD)
        self._spin_watergewicht.setValue(_WATERGEWICHT_STANDAARD)

        self._btn_reset_ontgraving  = self._maak_reset_knop()
        self._btn_reset_waterpeil   = self._maak_reset_knop()
        self._btn_reset_stijghoogte = self._maak_reset_knop()

        rij = 0
        for label, spin, reset in [
            ('Ontgravingsniveau (m NAP)',    self._spin_ontgraving,      self._btn_reset_ontgraving),
            ('Waterpeil in bouwput (m NAP)', self._spin_waterpeil,       self._btn_reset_waterpeil),
            ('Stijghoogte w.v.p. (m NAP)',   self._spin_stijghoogte,     self._btn_reset_stijghoogte),
            ('Materiaalfactor γG;stb (–)',   self._spin_materiaalfactor, None),
            ('Watergewicht γ_w (kN/m³)',     self._spin_watergewicht,    None),
        ]:
            grid.addWidget(QLabel(label), rij, 0)
            grid.addWidget(spin, rij, 1)
            if reset:
                grid.addWidget(reset, rij, 2)
            rij += 1

        self._chk_taludinvloed = QCheckBox('Taludinvloed meenemen')
        grid.addWidget(self._chk_taludinvloed, rij, 0, 1, 3)
        rij += 1

        # Taludinvloed-velden (conditioneel zichtbaar)
        self._widget_talud = QWidget()
        tgrid = QGridLayout(self._widget_talud)
        tgrid.setContentsMargins(0, 0, 0, 0)
        tgrid.setSpacing(6)

        self._spin_breedte          = self._maak_spin(0.0, 500.0, 2)
        self._spin_maaiveld_links   = self._maak_spin(-20.0, 20.0, 2)
        self._spin_helling_links_v  = self._maak_spin(0.0, 10.0, 1)
        self._spin_helling_links_h  = self._maak_spin(0.0, 100.0, 1)
        self._spin_maaiveld_rechts  = self._maak_spin(-20.0, 20.0, 2)
        self._spin_helling_rechts_v = self._maak_spin(0.0, 10.0, 1)
        self._spin_helling_rechts_h = self._maak_spin(0.0, 100.0, 1)

        self._btn_reset_breedte        = self._maak_reset_knop()
        self._btn_reset_talud_links    = self._maak_reset_knop()
        self._btn_reset_talud_rechts   = self._maak_reset_knop()

        tgrid.addWidget(QLabel('Breedte bouwputbodem (m)'), 0, 0)
        tgrid.addWidget(self._spin_breedte, 0, 1, 1, 3)
        tgrid.addWidget(self._btn_reset_breedte, 0, 4)

        tgrid.addWidget(QLabel('Maaiveld links (m NAP)'), 1, 0)
        tgrid.addWidget(self._spin_maaiveld_links, 1, 1, 1, 3)

        tgrid.addWidget(QLabel('Helling links v : h'), 2, 0)
        tgrid.addWidget(self._spin_helling_links_v, 2, 1)
        tgrid.addWidget(QLabel(':'), 2, 2)
        tgrid.addWidget(self._spin_helling_links_h, 2, 3)
        tgrid.addWidget(self._btn_reset_talud_links, 2, 4)

        tgrid.addWidget(QLabel('Maaiveld rechts (m NAP)'), 3, 0)
        tgrid.addWidget(self._spin_maaiveld_rechts, 3, 1, 1, 3)

        tgrid.addWidget(QLabel('Helling rechts v : h'), 4, 0)
        tgrid.addWidget(self._spin_helling_rechts_v, 4, 1)
        tgrid.addWidget(QLabel(':'), 4, 2)
        tgrid.addWidget(self._spin_helling_rechts_h, 4, 3)
        tgrid.addWidget(self._btn_reset_talud_rechts, 4, 4)

        self._widget_talud.setVisible(False)
        grid.addWidget(self._widget_talud, rij, 0, 1, 3)
        return groep

    def _bouw_resultaat_groep(self) -> QGroupBox:
        groep = QGroupBox('Resultaat')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._lbl_gstb     = QLabel('-')
        self._lbl_vdst     = QLabel('-')
        self._lbl_uc_basis = QLabel('-')
        self._lbl_uc_talud = QLabel('-')
        self._lbl_status   = QLabel('-')

        font_groot = QFont()
        font_groot.setPointSize(14)
        font_groot.setBold(True)
        self._lbl_uc_basis.setFont(font_groot)
        self._lbl_uc_talud.setFont(font_groot)
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setMinimumHeight(44)

        self._lbl_uc_talud_label = QLabel('UC (met taludinvloed)')
        grid.addWidget(QLabel('Gstb;d'), 0, 0)
        grid.addWidget(self._lbl_gstb, 0, 1)
        grid.addWidget(QLabel('Vdst;d'), 1, 0)
        grid.addWidget(self._lbl_vdst, 1, 1)
        grid.addWidget(QLabel('UC (zonder taludinvloed)'), 2, 0)
        grid.addWidget(self._lbl_uc_basis, 2, 1)
        grid.addWidget(self._lbl_uc_talud_label, 3, 0)
        grid.addWidget(self._lbl_uc_talud, 3, 1)
        grid.addWidget(self._lbl_status, 4, 0, 1, 2)

        self._lbl_uc_talud_label.setVisible(False)
        self._lbl_uc_talud.setVisible(False)
        return groep

    def _maak_spin(self, minimum: float, maximum: float, decimalen: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimalen)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(110)
        return spin

    def _maak_reset_knop(self) -> QPushButton:
        btn = QPushButton('↺')
        btn.setFixedWidth(30)
        btn.setToolTip('Terugzetten naar projectwaarde')
        return btn

    # ------------------------------------------------------------------
    # Signalen
    # ------------------------------------------------------------------
    def _verbind_signalen(self) -> None:
        for spin in [
            self._spin_ontgraving, self._spin_waterpeil, self._spin_stijghoogte,
            self._spin_materiaalfactor, self._spin_watergewicht,
            self._spin_breedte,
            self._spin_maaiveld_links, self._spin_helling_links_v, self._spin_helling_links_h,
            self._spin_maaiveld_rechts, self._spin_helling_rechts_v, self._spin_helling_rechts_h,
        ]:
            spin.valueChanged.connect(self._herbereken)

        self._combo_stage.currentTextChanged.connect(self._on_stage_gewijzigd)
        self._combo_profiel.currentTextChanged.connect(self._on_profiel_gewijzigd)
        self._combo_evenwicht.currentTextChanged.connect(self._herbereken)
        self._chk_taludinvloed.toggled.connect(self._on_talud_toggled)

        self._btn_reset_ontgraving.clicked.connect(self._reset_ontgraving)
        self._btn_reset_waterpeil.clicked.connect(self._reset_waterpeil)
        self._btn_reset_stijghoogte.clicked.connect(self._reset_stijghoogte)
        self._btn_reset_breedte.clicked.connect(self._reset_breedte)
        self._btn_reset_talud_links.clicked.connect(self._reset_talud_links)
        self._btn_reset_talud_rechts.clicked.connect(self._reset_talud_rechts)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------
    def update_project(self, project: Project | None) -> None:
        """Vul invoervelden automatisch in vanuit project.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        nieuwe_naam = project.base_name if project else None
        if nieuwe_naam == self._laatste_project_naam:
            return
        self._laatste_project_naam = nieuwe_naam
        self._project = project
        self._auto_waarden = None

        self._combo_stage.blockSignals(True)
        self._combo_stage.clear()
        if project:
            for stage in project.stages:
                self._combo_stage.addItem(stage.name)
        self._combo_stage.blockSignals(False)

        self._laad_auto_waarden()

    # ------------------------------------------------------------------
    # Interne state-handlers
    # ------------------------------------------------------------------
    def _laad_auto_waarden(self) -> None:
        """Laad auto-waarden voor de huidige stage- en profielkeuze."""
        if not self._project or not self._project.stages:
            self._auto_waarden = None
            self._vul_evenwicht_combo()
            return

        stage_naam = self._combo_stage.currentText()
        profiel_zijde = 'links' if self._combo_profiel.currentIndex() == 0 else 'rechts'
        self._auto_waarden = extraheer_auto_waarden_ve(
            self._project, stage_naam, profiel_zijde
        )
        self._vul_evenwicht_combo()
        self._reset_ontgraving()
        self._reset_waterpeil()
        self._reset_stijghoogte()
        self._reset_breedte()
        self._reset_talud_links()
        self._reset_talud_rechts()

    def _vul_evenwicht_combo(self) -> None:
        """Vul de evenwichtsniveau-dropdown met laagnamen uit het grondprofiel."""
        self._combo_evenwicht.blockSignals(True)
        huidig = self._combo_evenwicht.currentText()
        self._combo_evenwicht.clear()
        if self._auto_waarden:
            for naam, _bk, _ok, _gdr, _gnat in self._auto_waarden.grondlagen:
                self._combo_evenwicht.addItem(naam)
            idx = self._combo_evenwicht.findText(huidig)
            if idx >= 0:
                self._combo_evenwicht.setCurrentIndex(idx)
        self._combo_evenwicht.blockSignals(False)

    def _on_stage_gewijzigd(self) -> None:
        self._laad_auto_waarden()

    def _on_profiel_gewijzigd(self) -> None:
        self._laad_auto_waarden()

    def _on_talud_toggled(self, aan: bool) -> None:
        self._widget_talud.setVisible(aan)
        self._lbl_uc_talud_label.setVisible(aan)
        self._lbl_uc_talud.setVisible(aan)
        self._herbereken()

    # ------------------------------------------------------------------
    # Reset-handlers
    # ------------------------------------------------------------------
    def _reset_ontgraving(self) -> None:
        if self._auto_waarden and self._auto_waarden.ontgravingsniveau is not None:
            self._spin_ontgraving.blockSignals(True)
            self._spin_ontgraving.setValue(self._auto_waarden.ontgravingsniveau)
            self._spin_ontgraving.blockSignals(False)
        self._herbereken()

    def _reset_waterpeil(self) -> None:
        if self._auto_waarden and self._auto_waarden.waterpeil_bouwput is not None:
            self._spin_waterpeil.blockSignals(True)
            self._spin_waterpeil.setValue(self._auto_waarden.waterpeil_bouwput)
            self._spin_waterpeil.blockSignals(False)
        self._herbereken()

    def _reset_stijghoogte(self) -> None:
        if self._auto_waarden and self._auto_waarden.stijghoogte is not None:
            self._spin_stijghoogte.blockSignals(True)
            self._spin_stijghoogte.setValue(self._auto_waarden.stijghoogte)
            self._spin_stijghoogte.blockSignals(False)
        self._herbereken()

    def _reset_breedte(self) -> None:
        if self._auto_waarden and self._auto_waarden.breedte_bouwputbodem is not None:
            self._spin_breedte.blockSignals(True)
            self._spin_breedte.setValue(self._auto_waarden.breedte_bouwputbodem)
            self._spin_breedte.blockSignals(False)
        self._herbereken()

    def _reset_talud_links(self) -> None:
        if self._auto_waarden and self._auto_waarden.talud_links is not None:
            tl = self._auto_waarden.talud_links
            for spin, val in [
                (self._spin_maaiveld_links,  tl.maaiveld_niveau),
                (self._spin_helling_links_v, 1.0),
                (self._spin_helling_links_h, tl.helling_h_per_v),
            ]:
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self._herbereken()

    def _reset_talud_rechts(self) -> None:
        if self._auto_waarden and self._auto_waarden.talud_rechts is not None:
            tr = self._auto_waarden.talud_rechts
            for spin, val in [
                (self._spin_maaiveld_rechts,  tr.maaiveld_niveau),
                (self._spin_helling_rechts_v, 1.0),
                (self._spin_helling_rechts_h, tr.helling_h_per_v),
            ]:
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self._herbereken()

    # ------------------------------------------------------------------
    # Berekening
    # ------------------------------------------------------------------
    def _evenwichtsniveau(self) -> float | None:
        """Lees de o.k. van de gekozen evenwichtsniveau-laag uit de grondlagen."""
        if not self._auto_waarden:
            return None
        laagnaam = self._combo_evenwicht.currentText()
        for naam, _bk, ok, _gdr, _gnat in self._auto_waarden.grondlagen:
            if naam == laagnaam:
                return ok
        return None

    def _herbereken(self) -> None:
        lagen = self._auto_waarden.grondlagen if self._auto_waarden else []
        evenwichtsniveau = self._evenwichtsniveau()

        if not lagen or evenwichtsniveau is None:
            self._lbl_gstb.setText('-')
            self._lbl_vdst.setText('-')
            self._lbl_uc_basis.setText('-')
            self._lbl_uc_talud.setText('-')
            self._toon_status_neutraal()
            return

        gstb, vdst, uc = bereken_verticaal_evenwicht(
            lagen=lagen,
            ontgravingsniveau=self._spin_ontgraving.value(),
            waterpeil_bouwput=self._spin_waterpeil.value(),
            stijghoogte=self._spin_stijghoogte.value(),
            evenwichtsniveau=evenwichtsniveau,
            materiaalfactor=self._spin_materiaalfactor.value(),
            watergewicht=self._spin_watergewicht.value(),
        )

        self._lbl_gstb.setText(f'{fmt_number(gstb, 2)} kN/m²')
        self._lbl_vdst.setText(f'{fmt_number(vdst, 2)} kN/m²')
        self._lbl_uc_basis.setText(
            fmt_number(uc, 3) if not math.isinf(uc) else '∞'
        )

        # Taludinvloed
        uc_maatgevend = uc
        if self._chk_taludinvloed.isChecked() and not math.isinf(vdst) and vdst > 0.0:
            ontgravingsniveau = self._spin_ontgraving.value()
            b = self._spin_breedte.value() / 2.0
            d2 = abs(ontgravingsniveau - evenwichtsniveau)
            bijdragen: list[float] = []
            for maaiveld_spin, v_spin, h_spin in [
                (self._spin_maaiveld_links,  self._spin_helling_links_v,  self._spin_helling_links_h),
                (self._spin_maaiveld_rechts, self._spin_helling_rechts_v, self._spin_helling_rechts_h),
            ]:
                v = v_spin.value()
                h = h_spin.value()
                if v <= 0.0 or h <= 0.0:
                    continue
                maaiveld = maaiveld_spin.value()
                d1 = maaiveld - ontgravingsniveau
                if d1 <= 0.0:
                    continue
                a = d1 * (h / v)
                f = bereken_taludinvloed(d1, a, b, d2)
                gewicht = bereken_gewicht_talud(lagen, maaiveld, ontgravingsniveau)
                bijdragen.append(f * gewicht)
            if bijdragen:
                gstb_met = gstb + min(bijdragen)
                uc_met = gstb_met / vdst
                self._lbl_uc_talud.setText(fmt_number(uc_met, 3))
                uc_maatgevend = uc_met
            else:
                self._lbl_uc_talud.setText('-')

        self._toon_status(uc_maatgevend, vdst)

    def _toon_status_neutraal(self) -> None:
        self._lbl_status.setText('–')
        self._lbl_status.setStyleSheet(
            'background-color: #78909c; color: white; font-weight: bold;'
            ' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )

    def _toon_status(self, uc: float, vdst: float) -> None:
        if math.isinf(uc):
            self._lbl_status.setText('GEEN WATERDRUK')
            self._lbl_status.setStyleSheet(
                'background-color: #78909c; color: white; font-weight: bold;'
                ' font-size: 14pt; border-radius: 4px; padding: 4px;'
            )
            return
        voldoet = uc >= 1.0
        tekst = 'VOLDOET' if voldoet else 'VOLDOET NIET'
        kleur = '#2e7d32' if voldoet else '#c62828'
        self._lbl_status.setText(tekst)
        self._lbl_status.setStyleSheet(
            f'background-color: {kleur}; color: white; font-weight: bold;'
            f' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )
```

- [ ] **Stap 3.3 — Draai alle tests om zeker te weten dat de imports niet breken**

```
pytest tests/test_verticaal_evenwicht.py -v
```

Verwacht: **alle PASSED** (PyQt6 is aanwezig, maar widget wordt niet geïnstantieerd in tests).

- [ ] **Stap 3.4 — Commit**

```bash
git add ui/tabs/tab_verticaal_evenwicht.py
git commit -m "feat: voeg TabVerticaalEvenwicht UI-widget toe"
```

---

## Task 4: Integratie in TabAanvullendeBerekeningen

**Files:**
- Modify: `ui/tabs/tab_aanvullende_berekeningen.py`

- [ ] **Stap 4.1 — Voeg import en tweede subtab toe**

Vervang de volledige inhoud van `ui/tabs/tab_aanvullende_berekeningen.py`:

```python
"""Hoofdtab Aanvullende berekeningen — container voor aanvullende geotechnische controles."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from parsers.models import Project
from ui.tabs.tab_hydraulische_grondbreuk import TabHydraulischeGrondbreuk
from ui.tabs.tab_verticaal_evenwicht import TabVerticaalEvenwicht


class TabAanvullendeBerekeningen(QWidget):
    """Container-tab met subtabs voor aanvullende geotechnische berekeningen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tab_hydraulische_grondbreuk = TabHydraulischeGrondbreuk()
        self._tab_verticaal_evenwicht = TabVerticaalEvenwicht()
        self._tabs.addTab(self._tab_hydraulische_grondbreuk, 'Hydraulische Grondbreuk')
        self._tabs.addTab(self._tab_verticaal_evenwicht, 'Verticaal evenwicht')

        layout.addWidget(self._tabs)

    def update_project(self, project: Project | None) -> None:
        """Propageer projectwijziging naar alle subtabs.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        self._tab_hydraulische_grondbreuk.update_project(project)
        self._tab_verticaal_evenwicht.update_project(project)
```

- [ ] **Stap 4.2 — Draai alle tests**

```
pytest tests/ -v
```

Verwacht: **alle PASSED**, geen ImportErrors.

- [ ] **Stap 4.3 — Start de applicatie en test handmatig**

```
python run.pyw
```

Controleer:
1. Tab "Aanvullende berekeningen" → subtab "Verticaal evenwicht" is zichtbaar
2. Laad een `.shi`-project → stage-dropdown vult zich, grondprofiel-dropdown werkt
3. Evenwichtsniveau-dropdown toont laagnamen
4. Wijzigen van spinboxen herberekent UC
5. Checkbox "Taludinvloed meenemen" toont/verbergt de taaludinvloedvelden
6. Reset-knopjes herstellen de auto-waarden
7. Statusbalk toont VOLDOET (groen) of VOLDOET NIET (rood)

- [ ] **Stap 4.4 — Commit**

```bash
git add ui/tabs/tab_aanvullende_berekeningen.py
git commit -m "feat: integreer TabVerticaalEvenwicht in Aanvullende berekeningen"
```
