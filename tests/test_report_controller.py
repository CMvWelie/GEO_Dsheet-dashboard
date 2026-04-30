"""Tests voor ReportController."""

from __future__ import annotations

from app.report_controller import ReportController
from app.report_state import ReportState
from app.state import AppState
from parsers.models import FileBundle, Project, SoilLayer, SoilProfile, Stage


def _project() -> Project:
    return Project(
        base_name='p',
        project_name='P',
        file_bundle=FileBundle(),
        stages=[Stage(name='Fase 1')],
        profiles=[
            SoilProfile(
                name='Links',
                normalized_name='links',
                occurrence=1,
                x=None,
                y=None,
                layers=[SoilLayer(1, 0.0, 0.0, 0.0, 'Zand')],
            )
        ],
    )


def test_auto_populate_plan_hanteert_vaste_rapportvolgorde() -> None:
    """Rapportplan start met damwand/fase, daarna grondsoorten en resultaten."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState()
    controller = ReportController(app_state, report_state)

    controller.auto_populate_plan()

    ids = [item.id for item in report_state.plan.items]
    assert ids[:4] == [
        'damwand_damwand_gegevens',
        'damwand_fase_1_invoer',
        'grondsoorten_soil_table_links',
        'result_anchor_forces',
    ]


def test_build_package_gebruikt_damwandsecties_als_input() -> None:
    """Algemene rapportpackage bevat damwand/fase-secties als input_sections."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState()
    controller = ReportController(app_state, report_state)

    pakket = controller.build_package()

    ids = [sec.id for sec in pakket.input_sections]
    assert ids == ['damwand_gegevens', 'fase_1_invoer']


def test_set_template_word_zet_template_in_package() -> None:
    """Een vooraf ingesteld Word-templatepad komt direct in het package terecht."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState()
    controller = ReportController(app_state, report_state)

    controller.set_template_word('C:/templates/rapport.dotx')
    pakket = controller.build_package()

    assert pakket.template_word == 'C:/templates/rapport.dotx'
