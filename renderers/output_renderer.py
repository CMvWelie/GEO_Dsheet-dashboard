"""Resultaatgrafieken: momenten, dwarskrachten en verplaatsingen.

Geporteerd vanuit drawSingleResultChart() en renderOutputCharts() in
Dsheet_dashboard_v89.html.
"""

from __future__ import annotations
import math
import matplotlib.ticker as ticker

from matplotlib.figure import Figure
from matplotlib.axes import Axes

from parsers.models import Project, Stage, ResultStep
from app.settings import RenderSettings, ViewportSettings
from utils.geometry import surface_y_at, clip_surface_points, build_layer_polygons
from utils.color_utils import color_for_matplotlib
from utils.formatting import fmt_number
from renderers import BaseRenderer
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
    render_settings: RenderSettings | None = None,
    half_width_m: float = 10.0,
) -> None:
    """Teken één resultaatgrafiek (moment, dwarskracht of verplaatsing).

    Parameters
    ----------
    ax:            Matplotlib Axes.
    title:         Grafiektitel (bijv. "Momenten").
    unit:          Eenheid (bijv. "kNm").
    series_key:    Attribuut op ResultPoint ('moment', 'shear', 'disp').
    result_stage:  ResultStage object of None.
    project:       Huidig project.
    stage:         Actieve bouwfase.
    half_width_m:  Halve zichtbare breedte in meters, gecentreerd op de damwand.
    """
    ax.cla()
    ax.set_facecolor('white')

    # ── Damwandgrenzen (basis voor y-bereik) ────────────────────────────
    # Bij gestapeld profiel: bovenkant = hoogste top, onderkant = diepste bottom
    wall_top = (max(
        (s.top for s in project.sheet_piling if s.top is not None),
        default=0.0,
    ) if project.sheet_piling else 0.0)
    wall_bottom = (min(
        (s.bottom for s in project.sheet_piling if math.isfinite(s.bottom)),
        default=-10.0,
    ) if project.sheet_piling else -10.0)

    wall_height = wall_top - wall_bottom
    marge = wall_height * 0.10
    y_hi = wall_top + marge
    y_lo = wall_bottom - marge

    points = result_stage.points if result_stage else []

    # Resultaatwaarden (in eenheden: kNm / kN / mm)
    x_vals = [getattr(p, series_key, 0.0) or 0.0 for p in points] if points else [0.0]
    max_abs = max(1.0, *(abs(v) for v in x_vals))

    # Schaalfactor: max_abs eenheden → 42 % van half_width_m
    # De resultaatlijn vult ~84 % van de zichtbare breedte; de rest is ruimte voor
    # geometrie en annotaties.
    scale = (half_width_m * 0.42) / max_abs  # m per eenheid

    # X-as in meters, gecentreerd op de damwand (x = 0)
    x_lo = -half_width_m
    x_hi = half_width_m
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)

    # ── Achtergrond: maaiveld / grond / water (in meters) ───────────────
    left_surface = _find_by_name(project.surfaces,
                                  stage.left_surface if stage else None)
    right_surface = _find_by_name(project.surfaces,
                                   stage.right_surface if stage else None)
    left_pts = clip_surface_points(
        getattr(left_surface, 'points', None) or [{'x': x_lo, 'y': 0}, {'x': 0, 'y': 0}],
        x_lo, 0.0,
    )
    right_pts = clip_surface_points(
        getattr(right_surface, 'points', None) or [{'x': 0, 'y': 0}, {'x': x_hi, 'y': 0}],
        0.0, x_hi,
    )
    left_water = _find_by_name(project.waterlevels,
                                stage.left_water if stage else None)
    right_water = _find_by_name(project.waterlevels,
                                 stage.right_water if stage else None)

    def _get_profile(side: str):
        from renderers.section_renderer import get_stage_profile
        return get_stage_profile(project, stage, side)

    left_profile = _get_profile('left')
    right_profile = _get_profile('right')

    for profile, pts_side in [
        (left_profile, left_pts),
        (right_profile, right_pts),
    ]:
        if not profile or not pts_side:
            continue
        for i, layer in enumerate(profile.layers):
            layer_top = layer.level
            layer_bottom = (profile.layers[i + 1].level
                            if i + 1 < len(profile.layers) else y_lo)
            color = color_for_matplotlib(
                project.soil_color_map.get(layer.material, 'rgb(220,220,220)')
            )
            for poly in build_layer_polygons(pts_side, layer_top, layer_bottom):
                draw_polygon_on_ax(ax, poly, face_color=color, edge_color='#aaa',
                                   line_width=0.6)

    for pts_side in [left_pts, right_pts]:
        if pts_side:
            ax.plot([p['x'] for p in pts_side], [p['y'] for p in pts_side],
                    color='#8b7d1a', linewidth=1.2, clip_on=True)

    for water, wx1, wx2 in [(left_water, x_lo, 0.0), (right_water, 0.0, x_hi)]:
        if water and math.isfinite(water.level):
            ax.plot([wx1, wx2], [water.level, water.level],
                    color='#2d64d8', linewidth=1.3, clip_on=True)

    # ── Damwand (dunne grijze balk op x = 0 m) ──────────────────────────
    wall_w = half_width_m * 0.008  # breedte schaalt mee met zichtvenster
    ax.fill_betweenx([wall_bottom, wall_top],
                     [-wall_w, -wall_w], [wall_w, wall_w],
                     color='#777777', alpha=0.9, zorder=5)

    # ── Resultaatlijn (waarden omgezet naar meters) ──────────────────────
    if points:
        result_x_m = [v * scale for v in x_vals]
        result_y = [p.depth for p in points]
        ax.plot(result_x_m, result_y, color='#111111', linewidth=1.5, zorder=6)

        # Piek-annotaties: min en max
        max_v = max(x_vals)
        min_v = min(x_vals)
        max_i = x_vals.index(max_v)
        min_i = x_vals.index(min_v)
        label_pad_m = half_width_m * 0.04
        seen: set[int] = set()
        for val, idx in [(max_v, max_i), (min_v, min_i)]:
            if abs(val) < 0.01 or idx in seen:
                continue
            seen.add(idx)
            lx_m = val * scale + (label_pad_m if val >= 0 else -label_pad_m)
            ha = 'left' if val >= 0 else 'right'
            ax.plot(val * scale, result_y[idx], 'o', color='#333333',
                    markersize=4, zorder=9, clip_on=True)
            ax.text(lx_m, result_y[idx], f'{val:.1f}',
                    ha=ha, va='center', fontsize=7.5, color='#111111',
                    fontweight='bold', clip_on=False, zorder=8,
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='none', alpha=0.85))

    # ── Verticale nul-lijn ───────────────────────────────────────────────
    ax.axvline(x=0, color='#999999', linewidth=0.8, linestyle='--')

    # ── Onder-as: resultaatwaarden (kNm / kN / mm) ──────────────────────
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, symmetric=True))
    ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(
            lambda x, _: (f'{x / scale:.0f}' if abs(x) > 1e-9 else '0')
            if abs(scale) > 1e-12 else '0'
        )
    )
    ax.set_xlabel(f'[{unit}]', fontsize=8, labelpad=2)

    # ── Boven-as: schaallat in meters t.o.v. damwand ────────────────────
    ax2 = ax.secondary_xaxis('top')
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, integer=True, symmetric=True))
    ax2.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{x:.0f}')
    )
    ax2.set_xlabel('[m]', fontsize=8, labelpad=2)
    ax2.tick_params(labelsize=7)

    # ── Overige opmaak ───────────────────────────────────────────────────
    ax.set_title(title, fontsize=10, fontweight='bold', pad=22)
    ax.set_ylabel('Diepte [m NAP]', fontsize=9)
    ax.tick_params(axis='both', labelsize=8)
    ax.grid(True, axis='x', linestyle=':', linewidth=0.5, alpha=0.5)


class OutputRenderer(BaseRenderer):
    """Renderer voor resultaatgrafieken (momenten, dwarskrachten, verplaatsingen).

    Gebruik ``render_figure()`` voor de volledige drie-grafiek weergave.
    De ``render()`` methode (vereist door BaseRenderer) tekent alleen het
    momentendiagram op de meegegeven as.
    """

    _CHARTS: list[tuple[str, str, str]] = [
        ('Momenten', 'kNm', 'moment'),
        ('Dwarskrachten', 'kN', 'shear'),
        ('Vervormingen', 'mm', 'disp'),
    ]

    def render(
        self,
        ax: Axes,
        project: Project,
        stage: Stage | None,
        settings: RenderSettings,
        viewport: ViewportSettings,
    ) -> None:
        """Render het momentendiagram op een enkele as.

        Parameters
        ----------
        ax:       Matplotlib Axes om op te tekenen.
        project:  Het actieve projectobject.
        stage:    De actieve bouwfase (kan None zijn).
        settings: Renderschaalinstellingen.
        viewport: Viewport-bereik instellingen (niet gebruikt, aanwezig voor ABC).
        """
        stage_index = (project.stages.index(stage)
                       if stage and stage in project.stages else 0)
        result_stage = _get_stage_result(project, None, stage_index + 1)
        title, unit, key = self._CHARTS[0]
        draw_result_chart(ax, title, unit, key, result_stage, project,
                          stage, settings)

    def render_figure(
        self,
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
        half_width_m = (render_settings.resultaat_half_breedte_m
                        if render_settings else 10.0)
        for ax, (title, unit, key) in zip(axes, self._CHARTS):
            draw_result_chart(ax, title, unit, key, result_stage, project,
                              output_stage, render_settings,
                              half_width_m=half_width_m)

        fig.tight_layout()
