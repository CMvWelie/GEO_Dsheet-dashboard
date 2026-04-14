"""Tests voor SoilTableBuilder."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.models import Project, FileBundle, Soil, SoilProfile, SoilLayer
from reporting.builders.soil_table_builder import SoilTableBuilder


def _maak_project(profielen=None, soils=None) -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=soils or [],
        profiles=profielen or [],
    )


def _maak_profiel(naam: str, lagen: list[SoilLayer]) -> SoilProfile:
    return SoilProfile(
        name=naam, normalized_name=naam.lower(),
        occurrence=1, x=None, y=None, layers=lagen,
    )


def _laag(nr: int, level: float, material: str) -> SoilLayer:
    return SoilLayer(nr=nr, level=level, wosp_top=0.0, wosp_bottom=0.0, material=material)


def _soil(naam: str, gd=17.0, gn=19.0, c=2.0, phi=32.5, delta=16.0,
          kh1=10.0, kh2=20.0, kh3=30.0) -> Soil:
    return Soil(name=naam, color='rgb(0,0,0)', color_int=None,
                gamma_dry=gd, gamma_wet=gn, cohesion=c, phi=phi,
                delta=delta, kh1=kh1, kh2=kh2, kh3=kh3)


def test_één_sectie_per_profiel() -> None:
    project = _maak_project(
        profielen=[
            _maak_profiel('Links', [_laag(1, 0.0, 'Zand')]),
            _maak_profiel('Rechts', [_laag(1, 0.0, 'Klei')]),
        ],
    )
    secties = SoilTableBuilder().build(project)
    assert len(secties) == 2


def test_sectie_id_gesaniteerd() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('Links Zand', [_laag(1, 0.0, 'Zand')])]
    )
    secties = SoilTableBuilder().build(project)
    assert secties[0].id == 'soil_table_links_zand'


def test_sectie_titel_correct() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('Links', [_laag(1, 0.0, 'Zand')])]
    )
    secties = SoilTableBuilder().build(project)
    assert secties[0].title == 'Grondsoortentabel \u2014 Links'


def test_tabel_bevat_11_kolommen() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [_laag(1, 0.0, 'Zand')])]
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    assert len(tabel.columns) == 11


def test_rijen_gevuld_met_soil_params() -> None:
    soil = _soil('Zand', gd=17.0, phi=32.5, kh1=10.0)
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
        soils=[soil],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    rij = tabel.rows[0]
    # kolom 0=BK, 1=OK, 2=Laagnaam, 3=γd, 4=γn, 5=c', 6=φ', 7=δ, 8=kh1, 9=kh2, 10=kh3
    assert rij[2] == 'Zand'
    assert '17' in rij[3]   # gamma_dry=17,0
    assert '32' in rij[6]   # phi=32,5


def test_bk_en_ok_correct() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    # Eerste rij: BK=0.0, OK=niveau van laag 2 = -5.0
    assert '0' in tabel.rows[0][0]
    assert '-5' in tabel.rows[0][1]


def test_laatste_laag_ok_is_streepje() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    assert tabel.rows[-1][1] == '-'


def test_ontbrekende_soil_geeft_streepjes() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [_laag(1, 0.0, 'Onbekend')])],
        soils=[],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    rij = tabel.rows[0]
    assert rij[3] == '-'   # gamma_dry
    assert rij[6] == '-'   # phi


def test_lege_profielen_geeft_lege_lijst() -> None:
    project = _maak_project(profielen=[])
    assert SoilTableBuilder().build(project) == []


from reporting.models import ReportSection, ReportPackage, ReportMetadata
from reporting.selection import ReportPlan


def test_build_package_bevat_extra_sections() -> None:
    sec = ReportSection(id='soil_table_links', title='Grondsoortentabel \u2014 Links')
    plan = ReportPlan()
    pkg = plan.build_package(
        metadata=ReportMetadata(),
        input_sections=[],
        result_sections=[],
        extra_sections=[sec],
    )
    assert len(pkg.extra_sections) == 1
    assert pkg.extra_sections[0].id == 'soil_table_links'
