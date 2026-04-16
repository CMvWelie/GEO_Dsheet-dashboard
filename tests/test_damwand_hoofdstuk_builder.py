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
