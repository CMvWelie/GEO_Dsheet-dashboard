"""Tests voor DamwandHoofdstukBuilder."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.models import (
    Project, FileBundle, SheetPilingElement,
    Soil, SoilProfile, SoilLayer, Stage, ResultSummary,
    ResultStep, ResultStage, ResultPoint,
)
from reporting.builders.damwand_hoofdstuk_builder import DamwandHoofdstukBuilder


def _basis_project(**kwargs) -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        **kwargs,
    )


def _wall() -> SheetPilingElement:
    return SheetPilingElement(
        name='AZ 14-700 (S240GP)',
        x=0.0,
        bottom=-13.5,
        top=-4.3,
        width=1.4,
        height_mm=316.0,
        pile_width_mm=1400.0,
        ei_knm2_per_m=46599.0,
        section_area_cm2=146.1,
        resisting_moment_cm3=1405.0,
        max_char_moment_knm=337.2,
        opneembaar_moment_knm=225.0,
        steel_quality='S240GP',
    )


def test_damwand_sectie_aanwezig() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    secties = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    assert secties.id == 'damwand_gegevens'


def test_damwand_sectie_bevat_profiel_veld() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    sleutels = {f.key for f in sec.fields}
    assert 'profiel' in sleutels


def test_damwand_sectie_bevat_ei_en_opneembaar_moment() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    sleutels = {f.key for f in sec.fields}
    assert 'ei_knm2' in sleutels
    assert 'opneembaar_moment' in sleutels


def test_damwand_sectie_lengte_correct() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    veld = next(f for f in sec.fields if f.key == 'lengte')
    assert '9' in veld.value   # abs(-4.3 - -13.5) = 9.2 m


def test_damwand_sectie_geen_damwand_geeft_lege_fields() -> None:
    project = _basis_project(sheet_piling=[])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    assert sec.fields == []


def _maak_stage(naam: str) -> Stage:
    return Stage(name=naam, left_surface='MV', right_surface='MV',
                 left_water='GWS', right_water='GWS',
                 left_profile='Links', right_profile='Rechts')


def test_fase_secties_één_per_fase() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1'), _maak_stage('Fase 2')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert len(secties) == 2


def test_fase_sectie_id_bevat_fasenummer() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert 'fase_1' in secties[0].id


def test_fase_sectie_bevat_image_request() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert len(secties[0].images) == 1
    assert secties[0].images[0].figure_key == 'section'
    assert secties[0].images[0].stage_index == 0


def test_fase_secties_leeg_project() -> None:
    project = _basis_project(stages=[])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert secties == []


def _maak_summary(stage_nr: int, moment: float = 100.0) -> ResultSummary:
    return ResultSummary(
        stage_number=stage_nr,
        max_moment_knm=moment,
        max_shear_kn=80.0,
        max_disp_mm=30.0,
        mob_moment_pct=75.0,
        mob_grond_pct=70.0,
        ondersteuningen=[('Anker A', 120.0, -8.5)],
    )


def test_conclusietabel_sectie_id() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert sec.id == 'conclusietabel'


def test_conclusietabel_bevat_tabel() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1), _maak_summary(2)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert len(sec.tables) == 1
    assert len(sec.tables[0].rows) == 2


def test_conclusietabel_kolommen() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    kolommen = sec.tables[0].columns
    assert 'Fase' in kolommen[0]
    assert 'kNm' in kolommen[1]


def test_conclusietabel_lege_summaries() -> None:
    project = _basis_project(result_summaries=[])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert sec.tables == []


def test_grafiek_secties_bevatten_twee_image_requests() -> None:
    project = _basis_project(
        stages=[_maak_stage('F1')],
        result_summaries=[_maak_summary(1)],
    )
    secties = DamwandHoofdstukBuilder()._bouw_grafiek_secties(
        project, governing_step_key='ULS', disp_step_key='6.5'
    )
    alle_images = [img for sec in secties for img in sec.images]
    figuur_keys = {img.figure_key for img in alle_images}
    assert 'moment_shear' in figuur_keys
    assert 'displacement' in figuur_keys


def test_build_geeft_vijf_sectiegroepenblokken() -> None:
    project = _basis_project(
        sheet_piling=[_wall()],
        stages=[_maak_stage('F1')],
        result_summaries=[_maak_summary(1)],
    )
    secties = DamwandHoofdstukBuilder().build(
        project, governing_step_key='ULS', disp_step_key='6.5'
    )
    ids = [s.id for s in secties]
    # Minstens: grondlagen (0+), damwand, fase_1_invoer, conclusietabel, grafieken
    assert 'damwand_gegevens' in ids
    assert 'fase_1_invoer' in ids
    assert 'conclusietabel' in ids
