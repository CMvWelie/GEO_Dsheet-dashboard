"""Tests voor render-foutafhandeling in AppController."""

from __future__ import annotations

from app.controller import AppController
from app.state import AppState
from parsers.models import FileBundle, Project, Stage


class _FailingRenderer:
    def render(self, *_args, **_kwargs) -> None:
        raise RuntimeError('render stuk')


def test_render_stage_png_renderfout_geeft_none_zonder_project_name_crash() -> None:
    """Renderfouten gebruiken project_name/base_name in de logging."""
    project = Project(
        base_name='p',
        project_name='P',
        file_bundle=FileBundle(),
        stages=[Stage(name='Fase 1')],
    )
    controller = AppController(AppState())
    controller._renderer = _FailingRenderer()

    result = controller.render_stage_png(project, project.stages[0])

    assert result is None
