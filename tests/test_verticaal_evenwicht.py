"""Tests voor verticaal evenwicht berekeningslogica."""
from __future__ import annotations

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.tabs.tab_verticaal_evenwicht import (
    bereken_taludinvloed,
    bereken_verticaal_evenwicht,
    bereken_gewicht_talud,
    extraheer_talud_links,
    extraheer_talud_rechts,
    extraheer_auto_waarden_ve,
    _zoek_bodem_punten,
    TaludGeometrie,
    AutoWaardenVE,
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
