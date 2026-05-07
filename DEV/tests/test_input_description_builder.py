"""Tests voor InputDescriptionBuilder."""

from __future__ import annotations

from parsers.models import (
    FileBundle,
    HorizontalLineLoad,
    Moment,
    Project,
    Stage,
    Anchor,
    Strut,
    SpringSupport,
    RigidSupport,
    UniformLoad,
    SurchargeLoad,
    NormalForce,
)
from reporting.builders.input_description_builder import InputDescriptionBuilder


def test_faserow_extra_lines_standaard_leeg() -> None:
    from reporting.builders.input_description_builder import FaseRow
    rij = FaseRow(label='Test', value='0,0 [m NAP]')
    assert rij.extra_lines == []


def test_faserow_extra_lines_gevuld() -> None:
    from reporting.builders.input_description_builder import FaseRow
    rij = FaseRow(
        label='Stempel',
        value='-1,0 [m NAP]',
        extra='15 graden t.o.v. maaiveld',
        extra_lines=['3,5 m lengte'],
    )
    assert rij.extra_lines == ['3,5 m lengte']


def test_anchor_rapporteert_niveau_en_hoek() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        anchors=[Anchor(nr=1, level=-0.3, emod=2.1e8, cross_section=10.0,
                        length=5.0, yield_f=200.0, angle=0.0,
                        height=0.0, side=0, name='Leganker')],
        stages=[Stage(name='F1', anchors=['Leganker'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rijen = {r.label: r for r in cards[0].rows}
    assert rijen['Leganker'].value == '-0,3 [m NAP]'
    assert '0' in rijen['Leganker'].extra and 'maaiveld' in rijen['Leganker'].extra


def test_strut_rapporteert_niveau_hoek_en_lengte() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        struts=[Strut(nr=1, level=-1.0, emod=2.1e8, cross_section=10.0,
                      length=3.5, yield_f=500.0, angle=15.0,
                      aux=0.0, side=0, name='Stempel')],
        stages=[Stage(name='F1', struts=['Stempel'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Stempel')
    assert rij.value == '-1,0 [m NAP]'
    assert 'maaiveld' in rij.extra
    assert any('lengte' in l or '3,5' in l for l in rij.extra_lines)


def test_spring_support_rapporteert_niveau_en_twee_veerwaardes() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        spring_supports=[SpringSupport(nr=1, level=-2.0,
                                       rot_stiff=1000.0, tr_stiff=5000.0,
                                       name='Veersteun')],
        stages=[Stage(name='F1', spring_supports=['Veersteun'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Veersteun')
    assert rij.value == '-2,0 [m NAP]'
    assert 'kNm/rad' in rij.extra
    assert len(rij.extra_lines) == 1
    assert 'kN/m' in rij.extra_lines[0]


def test_rigid_support_rapporteert_alleen_niveau() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        rigid_supports=[RigidSupport(nr=1, level=-1.5,
                                     rot_stiff=0.0, tr_stiff=0.0,
                                     name='Rigide')],
        stages=[Stage(name='F1', rigid_supports=['Rigide'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Rigide')
    assert rij.value == '-1,5 [m NAP]'
    assert rij.extra == ''
    assert rij.extra_lines == []


def test_uniform_load_niveau_is_op_maaiveld() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        uniform_loads=[UniformLoad(name='Bovenbelasting',
                                   left=5.0, right=0.0,
                                   permanent=1.0, favourable=0.0)],
        stages=[Stage(name='F1', uniform_loads=['Bovenbelasting'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Bovenbelasting')
    assert rij.value == 'op maaiveld'
    assert '5' in rij.extra and 'kN/m²' in rij.extra


def test_surcharge_load_niveau_en_extra_lines() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        surcharge_loads=[SurchargeLoad(
            name='Surcharge',
            points=[{'distance': 0.0, 'value': 10.0},
                    {'distance': 3.0, 'value': 10.0}],
        )],
        stages=[Stage(name='F1',
                      surcharge_loads_left=['Surcharge'],
                      surcharge_loads_right=[])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Surcharge')
    assert rij.value == 'op maaiveld'
    assert 'kN/m²' in rij.extra
    assert len(rij.extra_lines) == 2
    assert any('breed' in l for l in rij.extra_lines)
    assert any('damwand' in l for l in rij.extra_lines)


def test_moment_rapporteert_niveau_en_waarde() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        moments=[Moment(nr=1, level=-1.0, value=12.5,
                        permanent=1.0, favourable=0.0, name='Leuningmoment')],
        stages=[Stage(name='F1', moments=['Leuningmoment'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Leuningmoment')
    assert rij.value == '-1,0 [m NAP]'
    assert '12,5' in rij.extra and 'kNm/m' in rij.extra


def test_horizontal_line_load_rapporteert_niveau_en_waarde() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        horizontal_line_loads=[HorizontalLineLoad(
            nr=1, level=-1.0, value=7.5,
            permanent=1.0, favourable=0.0, name='Leuninglast')],
        stages=[Stage(name='F1', horizontal_line_loads=['Leuninglast'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Leuninglast')
    assert rij.value == '-1,0 [m NAP]'
    assert '7,5' in rij.extra and 'kN/m' in rij.extra


def test_normal_force_gelijk_rapporteert_een_rij() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        normal_forces=[NormalForce(nr=1, top=10.0, surface_left=10.0,
                                   surface_right=10.0, bottom=10.0,
                                   permanent=1, favourable=0,
                                   name='Normaalkracht')],
        stages=[Stage(name='F1', normal_forces=['Normaalkracht'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Normaalkracht')
    assert rij.value == '-'
    assert '10' in rij.extra
    assert rij.extra_lines == []


def test_normal_force_ongelijk_rapporteert_vier_extra_lines() -> None:
    project = Project(
        base_name='p', project_name='P', file_bundle=FileBundle(),
        normal_forces=[NormalForce(nr=1, top=10.0, surface_left=8.0,
                                   surface_right=9.0, bottom=7.0,
                                   permanent=1, favourable=0,
                                   name='Normaalkracht')],
        stages=[Stage(name='F1', normal_forces=['Normaalkracht'])],
    )
    cards = InputDescriptionBuilder().build_all_stages(project)
    rij = next(r for r in cards[0].rows if r.label == 'Normaalkracht')
    assert rij.value == '-'
    assert len(rij.extra_lines) == 3  # extra + 3 extra_lines = 4 regels totaal
    alle = [rij.extra] + rij.extra_lines
    assert any('Top' in r for r in alle)
    assert any('Vlak links' in r for r in alle)
    assert any('Vlak rechts' in r for r in alle)
    assert any('Bottom' in r for r in alle)


def test_fase_invoer_sectie_is_report_section_subklasse() -> None:
    from reporting.models import FaseInvoerSectie, ReportSection
    sec = FaseInvoerSectie(id='f1', title='Fase 1')
    assert isinstance(sec, ReportSection)
    assert sec.fase_card is None


def test_fase_invoer_sectie_bewaart_fase_card() -> None:
    from reporting.models import FaseInvoerSectie
    from reporting.builders.input_description_builder import FaseCard
    kaart = FaseCard(fase_num=1, stage_name='Fase 1')
    sec = FaseInvoerSectie(id='f1', title='Fase 1', fase_card=kaart)
    assert sec.fase_card is kaart
