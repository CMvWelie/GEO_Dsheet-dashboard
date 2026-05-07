"""Smoke-tests voor de debug-tab widgets."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.models import (
    Project, FileBundle, Soil, SoilProfile, SoilLayer, Surface, WaterLevel,
    SheetPilingElement, Anchor, Strut, SpringSupport, RigidSupport,
    UniformLoad, SurchargeLoad, HorizontalLineLoad, Moment, NormalForce,
    Stage, ResultSummary, ResultStep, ResultStage, ResultPoint,
    AnchorStrutResumeItem, SupportResumeItem, VerifyStepSummary,
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
        struts=[Strut(
            nr=1, level=-3.0, emod=210000.0, cross_section=20.0,
            length=15.0, yield_f=500.0, angle=45.0, aux=0.0,
            side=1, name='Strut-1',
        )],
        spring_supports=[SpringSupport(
            nr=1, level=-5.0, rot_stiff=1000.0, tr_stiff=5000.0, name='SpringSupport-1',
        )],
        rigid_supports=[RigidSupport(
            nr=1, level=-6.0, rot_stiff=10000.0, tr_stiff=50000.0, name='RigidSupport-1',
        )],
        uniform_loads=[UniformLoad(
            name='UniformLoad-1', left=2.0, right=3.0, permanent=1.0, favourable=0.5,
        )],
        surcharge_loads=[SurchargeLoad(
            name='SurchargeLoad-1',
            points=[
                {'distance': 0.0, 'value': 10.0},
                {'distance': 5.0, 'value': 15.0},
            ],
        )],
        horizontal_line_loads=[HorizontalLineLoad(
            nr=1, level=-4.0, value=25.0, permanent=1.0, favourable=0.5, name='HorizontalLineLoad-1',
        )],
        moments=[Moment(
            nr=1, level=-4.5, value=50.0, permanent=1.0, favourable=0.5, name='Moment-1',
        )],
        normal_forces=[NormalForce(
            nr=1, top=100.0, surface_left=0.0, surface_right=0.0,
            bottom=0.0, permanent=1, favourable=0, name='NormalForce-1',
        )],
        profiles=[SoilProfile(
            name='Profiel 1',
            normalized_name='profiel_1',
            occurrence=1,
            x=0.0,
            y=0.0,
            layers=[
                SoilLayer(nr=1, level=0.0, wosp_top=0.0, wosp_bottom=-3.0, material='Zand'),
                SoilLayer(nr=2, level=-3.0, wosp_top=-3.0, wosp_bottom=-8.0, material='Zand'),
            ],
        )],
        surfaces=[
            Surface(
                nr=1,
                name='Maaiveld',
                points=[
                    {'nr': 1, 'x': -10.0, 'y': 1.0},
                    {'nr': 2, 'x': 0.0, 'y': 1.0},
                    {'nr': 3, 'x': 10.0, 'y': 1.0},
                ],
            ),
            Surface(
                nr=2,
                name='Bouwput',
                points=[
                    {'nr': 1, 'x': -10.0, 'y': -2.0},
                    {'nr': 2, 'x': 0.0, 'y': -2.0},
                    {'nr': 3, 'x': 10.0, 'y': -2.0},
                ],
            ),
        ],
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
            struts=['Strut-1'],
            spring_supports=['SpringSupport-1'],
            rigid_supports=['RigidSupport-1'],
            uniform_loads=['UniformLoad-1'],
            surcharge_loads_left=['SurchargeLoad-1'],
            horizontal_line_loads=['HorizontalLineLoad-1'],
            moments=['Moment-1'],
            normal_forces=['NormalForce-1'],
        )],
        anchor_strut_resume=[AnchorStrutResumeItem(
            stage_number=1, verification_type=1, basis_cur_step=1,
            partial_factor_set=1, representative_factor=1.0, force=85.0,
            anchor_type=1, anchor_state=0, changed_to_yielding=0,
            calculation_status=0, name='Anker-A',
        )],
        supports_resume=[SupportResumeItem(
            stage_number=1, verification_type=1, basis_cur_step=1,
            partial_factor_set=1, representative_factor=1.0, force=50.0,
            moment=0.0, support_rigidity_type=1, calculation_status=0, name='SpringSupport-1',
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


def test_tab_debug_uitvoer_sorteert_overzicht_op_fase_en_stap(qapp):
    from PyQt6.QtWidgets import QTableWidget
    from ui.tabs.tab_debug_uitvoer import TabDebugUitvoer

    project = _maak_sample_project()
    project.verify_step_summaries = [
        VerifyStepSummary(2, '6.5', False, 20.0, 2.0, 0.2, None, None),
        VerifyStepSummary(1, '6.5', False, 10.0, 1.0, 0.1, None, None),
        VerifyStepSummary(1, '6.1', True, 11.0, 1.1, 0.11, None, None),
        VerifyStepSummary(2, '6.1', True, 21.0, 2.1, 0.21, None, None),
    ]

    tab = TabDebugUitvoer()
    tab.update_project(project)

    tabel = tab.findChildren(QTableWidget)[0]
    assert [
        (tabel.item(r, 0).text(), tabel.item(r, 1).text())
        for r in range(tabel.rowCount())
    ] == [('1', '6.1'), ('1', '6.5'), ('2', '6.1'), ('2', '6.5')]


def test_tab_debug_aanmaken(qapp):
    from ui.tabs.tab_debug import TabDebug
    assert TabDebug() is not None


def test_tab_debug_update_project(qapp):
    from ui.tabs.tab_debug import TabDebug
    tab = TabDebug()
    tab.update_project(_maak_sample_project())
    tab.update_project(None)
