"""Resultaatgrafieken: momenten, dwarskrachten en verplaatsingen.

Geporteerd vanuit drawSingleResultChart() en renderOutputCharts() in
Dsheet_dashboard_v89.html.
"""

from __future__ import annotations
import math

from matplotlib.figure import Figure
from matplotlib.axes import Axes

from parsers.models import Project, Stage, ResultStep
from app.settings import RenderSettings, ViewportSettings
from utils.geometry import surface_y_at, clip_surface_points, build_layer_polygon
from utils.color_utils import color_for_matplotlib
from utils.formatting import fmt_number
from renderers.draw_helpers import draw_polygon_on_ax


def _find_by_name(lst, name: str):
    return next((x for x in (lst or []) if x.name == name), None)


def _get_stage_result(project: Project, result_step_key: str | None,
                       stage_number: int):
    """Haal de rekenresultaten op voor een stap en fasenummer."""
    if not result_step_key or result_step_key not in project.result_steps:
        return None
    step = project.result_steps[result_step_key]
    return step.stages.get(stage_number)


def draw_result_chart(
    ax: Axes,
    title: str,
    unit: str,
    series_key: str,
    result_stage,
    project: Project,
    stage: Stage | None,
    y_min: float,
    y_max: float,
    render_settings: RenderSettings | None = None,
) -> None:
    """Teken één resultaatgrafiek (moment, dwarskracht of verplaatsing).

    Parameters
    ----------
    ax:           Matplotlib Axes.
    title:        Grafiektitel (bijv. "Bending Moments").
    unit:         Eenheid (bijv. "kNm").
    series_key:   Attribuut op ResultPoint ('moment', 'shear', 'disp').
    result_stage: ResultStage object of None.
    project:      Huidig project.
    stage:        Actieve bouwfase.
    y_min/y_max:  y-bereik voor de diepte-as.
    """
    ax.cla()
    ax.set_facecolor('white')

    points = result_stage.points if result_stage else []

    y_vals = [p.depth for p in points] if points else [0.0, -10.0]
    y_lo = min(y_vals)
    y_hi = max(y_vals)

    x_vals = [getattr(p, series_key, 0.0) or 0.0 for p in points] if points else [0.0]
    max_abs = max(1.0, *(abs(v) for v in x_vals))
    x_pad = max_abs * 0.10
    x_lo = -(max_abs + x_pad)
    x_hi = max_abs + x_pad

    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo - 0.5, y_hi + 0.5)

    # Achtergrond: maaiveld / grond / water (vereenvoudigd)
    left_surface = _find_by_name(project.surfaces,
                                   stage.left_surface if stage else None)
    right_surface = _find_by_name(project.surfaces,
                                    stage.right_surface if stage else None)
    left_pts = clip_surface_points(
        getattr(left_surface, 'points', None) or [{'x': -10, 'y': 0}, {'x': 0, 'y': 0}],
        x_lo, 0.0
    )
    right_pts = clip_surface_points(
        getattr(right_surface, 'points', None) or [{'x': 0, 'y': 0}, {'x': 10, 'y': 0}],
        0.0, x_hi
    )
    left_water = _find_by_name(project.waterlevels,
                                 stage.left_water if stage else None)
    right_water = _find_by_name(project.waterlevels,
                                  stage.right_water if stage else None)

    def _get_profile(side):
        from renderers.section_renderer import get_stage_profile
        return get_stage_profile(project, stage, side)

    left_profile = _get_profile('left')
    right_profile = _get_profile('right')

    # Grondlagen links en rechts van de wand (x=0)
    for profile, pts_side, x1, x2 in [
        (left_profile, left_pts, x_lo, 0.0),
        (right_profile, right_pts, 0.0, x_hi),
    ]:
        if not profile or not pts_side:
            continue
        for i, layer in enumerate(profile.layers):
            layer_top = layer.level
            layer_bottom = (profile.layers[i + 1].level
                            if i + 1 < len(profile.layers) else y_lo)
            poly = build_layer_polygon(pts_side, layer_top, layer_bottom)
            if not poly:
                continue
            color = color_for_matplotlib(
                project.soil_color_map.get(layer.material, 'rgb(220,220,220)')
            )
            draw_polygon_on_ax(ax, poly, face_color=color, edge_color='#aaa', line_width=0.6)

    # Maaiveldlijn
    for pts_side in [left_pts, right_pts]:
        if pts_side:
            ax.plot([p['x'] for p in pts_side], [p['y'] for p in pts_side],
                    color='#8b7d1a', linewidth=1.2, clip_on=True)

    # Waterpeilen
    for water, x1, x2 in [(left_water, x_lo, 0.0), (right_water, 0.0, x_hi)]:
        if water and math.isfinite(water.level):
            ax.plot([x1, x2], [water.level, water.level],
                    color='#2d64d8', linewidth=1.3, clip_on=True)

    # Damwand (dunne grijze balk op x=0)
    wall = project.sheet_piling[0] if project.sheet_piling else None
    wall_top = (wall.top if wall and wall.top is not None else 0.0)
    wall_bottom = (wall.bottom if wall and math.isfinite(wall.bottom) else y_lo)
    ax.fill_betweenx([wall_bottom, wall_top], [-0.05, -0.05], [0.05, 0.05],
                      color='#777777', alpha=0.9, zorder=5)

    # Resultaatlijn
    if points:
        result_x = [getattr(p, series_key, 0.0) or 0.0 for p in points]
        result_y = [p.depth for p in points]
        ax.plot(result_x, result_y, color='#111111', linewidth=1.5, zorder=6)

        # Piek-annotaties: min en max
        max_v = max(result_x)
        min_v = min(result_x)
        max_i = result_x.index(max_v)
        min_i = result_x.index(min_v)
        label_pad = max_abs * 0.06
        seen: set[int] = set()
        for val, idx in [(max_v, max_i), (min_v, min_i)]:
            if abs(val) < 0.01 or idx in seen:
                continue
            seen.add(idx)
            ha = 'left' if val >= 0 else 'right'
            lx = val + (label_pad if val >= 0 else -label_pad)
            ax.plot(val, result_y[idx], 'o', color='#333333',
                    markersize=4, zorder=9, clip_on=True)
            ax.text(lx, result_y[idx], f'{val:.1f}',
                    ha=ha, va='center', fontsize=7.5, color='#111111',
                    fontweight='bold', clip_on=True, zorder=8,
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='none', alpha=0.75))

    # Verticale nul-lijn
    ax.axvline(x=0, color='#999999', linewidth=0.8, linestyle='--')

    # Labels en ticks
    ax.set_title(f'{title} [{unit}]', fontsize=10, fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('Diepte [m]', fontsize=9)
    ax.tick_params(axis='both', labelsize=8)

    ax.grid(True, axis='x', linestyle=':', linewidth=0.5, alpha=0.5)


def render_output_charts(
    fig: Figure,
    project: Project,
    output_stage_index: int,
    active_result_step: str | None,
    render_settings: RenderSettings | None = None,
) -> None:
    """Teken drie resultaatgrafieken (moment, dwarskracht, verplaatsing).

    Parameters
    ----------
    fig:                Matplotlib Figure met drie subplots naast elkaar.
    project:            Huidig project.
    output_stage_index: Index van de actieve uitvoerfase.
    active_result_step: Genormaliseerde sleutel van de VERIFY STEP.
    render_settings:    Optionele renderinstellingen (schaal, kleuren).
    """
    if len(fig.axes) < 3:
        fig.clear()
        axes = fig.subplots(1, 3, sharey=True)
    else:
        axes = fig.axes[:3]

    output_stage = (project.stages[output_stage_index]
                    if 0 <= output_stage_index < len(project.stages) else None)
    stage_number = output_stage_index + 1

    result_stage = _get_stage_result(project, active_result_step, stage_number)

    y_min = min(
        (p.depth for step in project.result_steps.values()
         for st in step.stages.values() for p in st.points),
        default=-10.0
    )
    y_max = max(
        (p.depth for step in project.result_steps.values()
         for st in step.stages.values() for p in st.points),
        default=0.0
    )

    charts = [
        ('Momenten', 'kNm', 'moment'),
        ('Dwarskrachten', 'kN', 'shear'),
        ('Vervormingen', 'mm', 'disp'),
    ]
    for ax, (title, unit, key) in zip(axes, charts):
        draw_result_chart(ax, title, unit, key, result_stage, project,
                           output_stage, y_min, y_max, render_settings)

    fig.tight_layout()
