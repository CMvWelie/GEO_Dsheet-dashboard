"""Tests voor ReportController."""

from __future__ import annotations

from app.report_controller import ReportController
from app.report_state import ReportState
from app.state import AppState
from parsers.models import FileBundle, Project, SoilLayer, SoilProfile, Stage
from reporting.models import ReportMetadata


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
    """Rapportplan volgt de volgorde van de hoofdstukbuilder."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState()
    controller = ReportController(app_state, report_state)

    controller.auto_populate_plan()

    ids = [item.id for item in report_state.plan.items]
    assert ids[:4] == [
        'soil_table_links',
        'damwand_gegevens',
        'fase_1_invoer',
        'anchor_forces',
    ]


def test_set_template_word_slaat_template_op() -> None:
    """Een vooraf ingesteld Word-templatepad wordt in ReportState bewaard."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState()
    controller = ReportController(app_state, report_state)

    controller.set_template_word('C:/templates/rapport.dotx')

    assert report_state.template_word == 'C:/templates/rapport.dotx'


def test_build_metadata_gebruikt_report_state_metadata() -> None:
    """Metadata voor Word-export komt uit ReportState.metadata."""
    app_state = AppState(projects={'p': _project()}, active_project='p')
    report_state = ReportState(metadata=ReportMetadata(project_name='Project X'))
    controller = ReportController(app_state, report_state)

    assert controller.build_metadata().project_name == 'Project X'
