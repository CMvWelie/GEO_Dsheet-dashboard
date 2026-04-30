"""Headless figuurrendering voor rapportage-export."""

from __future__ import annotations

from app.settings import RenderSettings, ViewportSettings
from parsers.models import Project
from reporting.models import ReportImageRequest
from renderers.section_renderer import (
    SectionRenderer,
    x_range_for_project,
    y_range_for_project,
)


def render_figuur(img_req: ReportImageRequest, project: Project) -> bytes | None:
    """Render een rapportfiguur naar PNG-bytes.

    Parameters
    ----------
    img_req:
        Figuurverzoek met type, fase-index en optionele resultaatstap.
    project:
        Projectdata waaruit de figuur wordt opgebouwd.

    Returns
    -------
    bytes | None
        PNG-bytes, of ``None`` als het figuurtype niet ondersteund wordt.
    """
    import io

    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    key = img_req.figure_key
    stage_index = img_req.stage_index or 0
    stage = (
        project.stages[stage_index]
        if project.stages and 0 <= stage_index < len(project.stages)
        else None
    )
    render_settings = RenderSettings()
    viewport_settings = ViewportSettings()

    try:
        if key == 'section':
            fig = Figure(figsize=(16 / 2.54, 12 / 2.54))
            FigureCanvasAgg(fig)
            ax = fig.add_subplot(111)
            y_min, y_max = y_range_for_project(project)
            x_min, x_max = x_range_for_project(project)
            viewport_settings.y_min = y_min - 1.0
            viewport_settings.y_max = y_max + 0.5
            viewport_settings.x_min = x_min
            viewport_settings.x_max = x_max
            SectionRenderer().render(
                ax, project, stage, render_settings, viewport_settings
            )
            fig.tight_layout()
        elif key in (
            'moment_shear',
            'displacement',
            'moment_curve',
            'shear_curve',
            'disp_curve',
        ):
            fig = _render_resultaat_figuur(
                key, img_req, project, stage, stage_index, render_settings
            )
        else:
            return None

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def _render_resultaat_figuur(
    key: str,
    img_req: ReportImageRequest,
    project: Project,
    stage,
    stage_index: int,
    render_settings: RenderSettings,
):
    """Render een resultaatfiguur naar een Matplotlib Figure."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    from renderers.output_renderer import draw_result_chart

    step_key = img_req.step_key
    stage_number = stage_index + 1
    result_stage = (
        project.result_steps[step_key].stages.get(stage_number)
        if step_key and step_key in project.result_steps
        else None
    )

    single_charts = {
        'moment_curve': ('Momenten', 'kNm', 'moment'),
        'shear_curve': ('Dwarskrachten', 'kN', 'shear'),
        'disp_curve': ('Vervormingen', 'mm', 'disp'),
    }
    if key in single_charts:
        titel, eenheid, reeks = single_charts[key]
        fig = Figure(figsize=(5.2, 7.0))
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        draw_result_chart(
            ax, titel, eenheid, reeks, result_stage, project, stage,
            render_settings,
        )
    elif key == 'moment_shear':
        fig = Figure(figsize=(16 / 2.54, 10 / 2.54))
        FigureCanvasAgg(fig)
        axes = fig.subplots(1, 2, sharey=True)
        grafieken = [
            ('Momenten', 'kNm', 'moment'),
            ('Dwarskrachten', 'kN', 'shear'),
        ]
        for ax, (titel, eenheid, reeks) in zip(axes, grafieken):
            draw_result_chart(
                ax, titel, eenheid, reeks, result_stage, project, stage,
                render_settings,
            )
    else:
        fig = Figure(figsize=(8 / 2.54, 10 / 2.54))
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        draw_result_chart(
            ax, 'Vervormingen', 'mm', 'disp', result_stage, project, stage,
            render_settings,
        )
    fig.tight_layout()
    return fig
