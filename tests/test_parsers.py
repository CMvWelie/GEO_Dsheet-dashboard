"""Unit-tests voor de D-Sheet parsers.

Gebruik: pytest tests/test_parsers.py
Geen externe testdata nodig – alle invoer is ingebed als string.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from parsers.base_parser import extract_section, find_line_value
from parsers.shi_parser import (
    parse_soils, parse_soil_profiles, parse_sheet_piling,
    parse_anchors, parse_struts, parse_water_levels, parse_surfaces,
    parse_stages, parse_project, parse_result_summaries,
)
from parsers.models import FileBundle
from utils.color_utils import parse_color_int
from utils.geometry import surface_y_at, clip_surface_points
from utils.formatting import fmt_number, format_normal_force_values


# ---------------------------------------------------------------------------
# Testdata
# ---------------------------------------------------------------------------

SAMPLE_SHI = """\
FILENAME : C:\\projecten\\testproject.shi

[SOIL]
Klei
SoilColor=5855577
[END OF SOIL]

[SOIL]
Zand
SoilColor=16777024
[END OF SOIL]

[SOIL PROFILES]
2 Number of soil profiles

Klei profiel
1.0 X coordinate
0.0 Y coordinate
Nr Level WOSP top WOSP bottom Material
1 0.0 0.0 0.0 Klei
2 -5.0 0.0 0.0 Zand
3 -12.0 0.0 0.0 Klei

Zand profiel
3.0 X coordinate
0.0 Y coordinate
Nr Level WOSP top WOSP bottom Material
1 0.0 0.0 0.0 Zand
2 -8.0 0.0 0.0 Klei
[END OF SOIL PROFILES]

[SURFACES]
1 2 Maaiveld links
1 -5.0 0.5
2 0.0 0.0
[END OF SURFACES]

[WATERLEVELS]
Waterstand hoog
-1.0
Waterstand laag
-2.5
[END OF WATERLEVELS]

[SHEET PILING]
3.0 Level top sheet piling

[SHEET PILING ELEMENT]
Stalen damwand
SheetPilingElementX=0.0
SheetPilingElementLevel=-14.0
SheetPilingElementWidth=0.4
[END OF SHEET PILING ELEMENT]
[END OF SHEET PILING]

[ANCHORS]
1 -1.5 210000 1e-3 10.0 500 15 0.0 1 Anker-1
[END OF ANCHORS]

[STRUTS]
1 -0.5 210000 5e-3 6.0 200 5 0.0 2 Stempel-1
[END OF STRUTS]

[CONSTRUCTION STAGES]
2 Number of Construction stages

Fase 1
Method Left: Culmann
Maaiveld links
Maaiveld links
Waterstand hoog
Waterstand laag
Klei profiel
Zand profiel
0 Anchors present in stage
0 Struts present in stage
0 Spring supports present in stage
0 Rigid supports present in stage
0 Uniform loads in stage
0 0 Surcharge loads in stage
0 Horizontal line loads in stage
0 Moments in stage
0 Normal forces in stage

Fase 2
Method Left: Culmann
Maaiveld links
Maaiveld links
Waterstand laag
Waterstand laag
Klei profiel
Zand profiel
1 Anchors present in stage
1 -1.5 Anker-1
0 Struts present in stage
0 Spring supports present in stage
0 Rigid supports present in stage
0 Uniform loads in stage
0 0 Surcharge loads in stage
0 Horizontal line loads in stage
0 Moments in stage
0 Normal forces in stage

[END OF CONSTRUCTION STAGES]
"""


# ---------------------------------------------------------------------------
# base_parser tests
# ---------------------------------------------------------------------------

def test_extract_section_basic():
    text = '[FOO]\nhello\nworld\n[END OF FOO]'
    result = extract_section(text, 'FOO')
    assert 'hello' in result
    assert 'world' in result


def test_extract_section_missing():
    assert extract_section('nothing here', 'FOO') == ''


def test_find_line_value():
    text = 'FILENAME : C:\\test\\project.shi\n'
    result = find_line_value(text, r'^FILENAME\s*:\s*(.+)$')
    assert result == 'C:\\test\\project.shi'


def test_find_line_value_missing():
    assert find_line_value('nothing', r'^FOO=(.+)$') == ''


# ---------------------------------------------------------------------------
# color_utils tests
# ---------------------------------------------------------------------------

def test_parse_color_int_zero():
    assert parse_color_int(0) == 'rgb(0, 0, 0)'


def test_parse_color_int_white():
    # 0xFFFFFF = 16777215
    assert parse_color_int(16777215) == 'rgb(255, 255, 255)'


def test_parse_color_int_bgr():
    # BGR: R=86, G=132, B=89 → int = 89*(2^16) + 132*(2^8) + 86 = 5855574 ≈
    # Gebruik een eenvoudige waarde: 0x010203 → R=3, G=2, B=1
    assert parse_color_int(0x010203) == 'rgb(3, 2, 1)'


# ---------------------------------------------------------------------------
# Grondsoorten
# ---------------------------------------------------------------------------

def test_parse_soils():
    soils = parse_soils(SAMPLE_SHI)
    assert len(soils) == 2
    assert soils[0].name == 'Klei'
    assert soils[1].name == 'Zand'
    assert soils[0].color.startswith('rgb(')


def test_parse_soils_empty():
    assert parse_soils('geen soils hier') == []


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


# ---------------------------------------------------------------------------
# Grondprofielen
# ---------------------------------------------------------------------------

def test_parse_soil_profiles():
    profiles = parse_soil_profiles(SAMPLE_SHI)
    assert len(profiles) == 2
    klei_prof = profiles[0]
    assert klei_prof.name == 'Klei profiel'
    assert len(klei_prof.layers) == 3
    assert klei_prof.layers[0].level == 0.0
    assert klei_prof.layers[1].level == -5.0
    assert klei_prof.layers[0].material == 'Klei'
    assert klei_prof.layers[1].material == 'Zand'


def test_parse_soil_profiles_x_coordinate():
    profiles = parse_soil_profiles(SAMPLE_SHI)
    assert profiles[0].x == 1.0
    assert profiles[1].x == 3.0


# ---------------------------------------------------------------------------
# Maaiveldprofielen
# ---------------------------------------------------------------------------

def test_parse_surfaces():
    surfaces = parse_surfaces(SAMPLE_SHI)
    assert len(surfaces) == 1
    assert surfaces[0].name == 'Maaiveld links'
    assert len(surfaces[0].points) == 2
    assert surfaces[0].points[0]['x'] == -5.0
    assert surfaces[0].points[0]['y'] == 0.5


# ---------------------------------------------------------------------------
# Waterpeilen
# ---------------------------------------------------------------------------

def test_parse_water_levels():
    wl = parse_water_levels(SAMPLE_SHI)
    assert len(wl) == 2
    assert wl[0].name == 'Waterstand hoog'
    assert wl[0].level == -1.0
    assert wl[1].name == 'Waterstand laag'
    assert wl[1].level == -2.5


# ---------------------------------------------------------------------------
# Damwand
# ---------------------------------------------------------------------------

def test_parse_sheet_piling():
    sp = parse_sheet_piling(SAMPLE_SHI)
    assert len(sp) == 1
    assert sp[0].name == 'Stalen damwand'
    assert sp[0].top == 3.0
    assert sp[0].bottom == -14.0
    assert sp[0].width == 0.4
    assert sp[0].segment_top == 3.0
    assert sp[0].segment_bottom == -14.0


# ---------------------------------------------------------------------------
# Bouwfases (state machine)
# ---------------------------------------------------------------------------

def test_parse_stages():
    stages = parse_stages(SAMPLE_SHI)
    assert len(stages) == 2
    assert stages[0].name == 'Fase 1'
    assert stages[1].name == 'Fase 2'


def test_parse_stages_surface_references():
    stages = parse_stages(SAMPLE_SHI)
    assert stages[0].left_surface == 'Maaiveld links'
    assert stages[0].left_water == 'Waterstand hoog'
    assert stages[0].right_water == 'Waterstand laag'
    assert stages[0].left_profile == 'Klei profiel'
    assert stages[0].right_profile == 'Zand profiel'


def test_parse_stages_anchors_fase2():
    stages = parse_stages(SAMPLE_SHI)
    assert len(stages[1].anchors) == 1
    assert stages[1].anchors[0] == 'Anker-1'


def test_parse_stages_fase1_geen_ankers():
    stages = parse_stages(SAMPLE_SHI)
    assert stages[0].anchors == []


# ---------------------------------------------------------------------------
# Ankers en stempels
# ---------------------------------------------------------------------------

def test_parse_anchors():
    anchors = parse_anchors(SAMPLE_SHI)
    assert len(anchors) == 1
    assert anchors[0].name == 'Anker-1'
    assert anchors[0].level == -1.5
    assert anchors[0].angle == 15.0
    assert anchors[0].length == 10.0


def test_parse_struts():
    struts = parse_struts(SAMPLE_SHI)
    assert len(struts) == 1
    assert struts[0].name == 'Stempel-1'
    assert struts[0].level == -0.5


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


# ---------------------------------------------------------------------------
# Volledig project
# ---------------------------------------------------------------------------

def test_parse_project():
    bundle = FileBundle(shi=SAMPLE_SHI)
    project = parse_project(bundle, 'testproject')
    assert project.project_name == 'testproject'
    assert len(project.soils) == 2
    assert len(project.profiles) == 2
    assert len(project.stages) == 2
    assert len(project.sheet_piling) == 1
    assert 'Klei' in project.soil_color_map
    assert 'Zand' in project.soil_color_map


def test_parse_project_name_from_filename():
    shi_with_filename = 'FILENAME : C:\\projecten\\mijn_damwand.shi\n' + SAMPLE_SHI
    bundle = FileBundle(shi=shi_with_filename)
    project = parse_project(bundle, 'fallback')
    assert project.project_name == 'mijn_damwand'


# ---------------------------------------------------------------------------
# Geometrie-hulpfuncties
# ---------------------------------------------------------------------------

def test_surface_y_at_interpolation():
    pts = [{'x': 0.0, 'y': 0.0}, {'x': 10.0, 'y': -2.0}]
    assert surface_y_at(pts, 5.0) == pytest.approx(-1.0)


def test_surface_y_at_extrapolation():
    pts = [{'x': 0.0, 'y': 0.0}, {'x': 10.0, 'y': -2.0}]
    assert surface_y_at(pts, -5.0) == 0.0
    assert surface_y_at(pts, 15.0) == -2.0


def test_surface_y_at_empty():
    assert surface_y_at([], 5.0) == 0.0


def test_clip_surface_points():
    pts = [{'x': -10.0, 'y': 0.0}, {'x': 0.0, 'y': 0.0}, {'x': 10.0, 'y': 0.0}]
    clipped = clip_surface_points(pts, -5.0, 5.0)
    xs = [p['x'] for p in clipped]
    assert min(xs) == pytest.approx(-5.0)
    assert max(xs) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Opmaak-hulpfuncties
# ---------------------------------------------------------------------------

def test_fmt_number():
    assert fmt_number(3.456, 1) == '3,5'
    assert fmt_number(0.0, 2) == '0,0'
    assert fmt_number(None) == '-'
    assert fmt_number(float('nan')) == '-'


def test_fmt_number_negative():
    assert fmt_number(-1.5, 1) == '-1,5'


def test_format_normal_force_values_equal():
    from parsers.models import NormalForce
    nf = NormalForce(nr=1, top=100.0, surface_left=100.0, surface_right=100.0,
                      bottom=100.0, permanent=1, favourable=0, name='NF-1')
    result = format_normal_force_values(nf)
    assert result == '100,0 kN/m'


def test_format_normal_force_values_varying():
    from parsers.models import NormalForce
    nf = NormalForce(nr=1, top=100.0, surface_left=90.0, surface_right=80.0,
                      bottom=70.0, permanent=1, favourable=0, name='NF-1')
    result = format_normal_force_values(nf)
    assert 'T/SL/SR/B' in result


# ---------------------------------------------------------------------------
# ResultSummary parser
# ---------------------------------------------------------------------------

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
     0.00000      0.00000     23.56000
     5.00000     87.70000     23.50000
    -86.20000    -10.00000     23.50000
[END OF DATA]
[END OF TABLE]
[END OF MOMENTS FORCES DISPLACEMENTS]
[END OF CONSTRUCTION STAGE]
"""
    summaries = parse_result_summaries(shd_tekst)
    assert len(summaries) == 1
    s = summaries[0]
    assert s.stage_number == 1
    assert s.max_moment_knm == pytest.approx(86.2)
    assert s.max_shear_kn == pytest.approx(87.7)
    assert s.max_disp_mm == pytest.approx(23.56)  # waarden in .shd zijn al in mm
    assert s.mob_moment_pct == pytest.approx(11.8)
    assert s.mob_grond_pct == pytest.approx(12.70)
    assert len(s.ondersteuningen) == 1
    naam, kracht, niveau = s.ondersteuningen[0]
    assert naam == 'GroutankerL'
    assert kracht == pytest.approx(44.19)
    assert niveau == pytest.approx(-2.0)
