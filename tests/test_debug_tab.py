"""Smoke-tests voor de debug-tab widgets."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from parsers.models import (
    Project, FileBundle, Soil, WaterLevel, SheetPilingElement,
    Anchor, Stage, ResultSummary, ResultStep, ResultStage, ResultPoint,
)


def _maak_sample_project() -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=[Soil(name='Zand', color='rgb(220,220,50)', color_int=None,
                    gamma_dry=18.0, gamma_wet=20.0)],
        waterlevels=[WaterLevel(name='NAP', level=0.0)],
        sheet_piling=[SheetPilingElement(
            name='AZ18', x=0.0, bottom=-8.0, top=1.0, width=0.9,
        )],
        anchors=[Anchor(
            nr=1, level=-2.0, emod=210000.0, cross_section=15.0,
            length=10.0, yield_f=450.0, angle=30.0, height=0.5,
            side=1, name='Anker-A',
        )],
        stages=[Stage(
            name='Fase 1',
            method_line='1 0 Ec3 DA1',
            left_surface='Maaiveld',
            right_surface='Bouwput',
            left_water='NAP',
            right_water='NAP',
            left_profile='Profiel 1',
            right_profile='Profiel 1',
            anchors=['Anker-A'],
        )],
        result_summaries=[ResultSummary(
            stage_number=1,
            max_moment_knm=120.5,
            max_shear_kn=45.2,
            max_disp_mm=8.3,
            mob_moment_pct=62.0,
            mob_grond_pct=48.0,
            ondersteuningen=[('Anker-A', 85.0, -2.0)],
        )],
        result_steps={
            'Stap 1': ResultStep(
                raw_step='Stap 1',
                depths=[-1.0, -2.0, -3.0],
                stages={1: ResultStage(
                    stage_number=1,
                    points=[
                        ResultPoint(depth=-1.0, moment=10.0, shear=5.0, disp=1.0),
                        ResultPoint(depth=-2.0, moment=80.0, shear=30.0, disp=4.0),
                        ResultPoint(depth=-3.0, moment=120.0, shear=45.0, disp=8.0),
                    ],
                )},
            ),
        },
    )


def test_tab_debug_invoer_aanmaken(qapp):
    from ui.tabs.tab_debug_invoer import TabDebugInvoer
    assert TabDebugInvoer() is not None


def test_tab_debug_invoer_geen_project(qapp):
    from ui.tabs.tab_debug_invoer import TabDebugInvoer
    TabDebugInvoer().update_project(None)


def test_tab_debug_invoer_met_project(qapp):
    from ui.tabs.tab_debug_invoer import TabDebugInvoer
    TabDebugInvoer().update_project(_maak_sample_project())


def test_tab_debug_uitvoer_aanmaken(qapp):
    from ui.tabs.tab_debug_uitvoer import TabDebugUitvoer
    assert TabDebugUitvoer() is not None


def test_tab_debug_uitvoer_geen_project(qapp):
    from ui.tabs.tab_debug_uitvoer import TabDebugUitvoer
    TabDebugUitvoer().update_project(None)


def test_tab_debug_uitvoer_met_project(qapp):
    from ui.tabs.tab_debug_uitvoer import TabDebugUitvoer
    TabDebugUitvoer().update_project(_maak_sample_project())


def test_tab_debug_aanmaken(qapp):
    from ui.tabs.tab_debug import TabDebug
    assert TabDebug() is not None


def test_tab_debug_update_project(qapp):
    from ui.tabs.tab_debug import TabDebug
    tab = TabDebug()
    tab.update_project(_maak_sample_project())
    tab.update_project(None)
