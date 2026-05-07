"""Damwand doorsnede-renderer.

Directe portage van drawSection() uit Dsheet_dashboard_v89.html naar matplotlib.
Alle coördinaten zijn in data-eenheden (meters NAP / meters horizontaal).
matplotlib-assen werken in data-coördinaten zodat xScale/yScale overbodig zijn.
"""

from __future__ import annotations
import math
import re as _re

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Polygon as MplPolygon, Rectangle, Arc, FancyArrow
from matplotlib.lines import Line2D

from renderers import BaseRenderer
from app.settings import RenderSettings, ViewportSettings
from parsers.models import Project, Stage
from utils.color_utils import color_for_matplotlib
from utils.geometry import surface_y_at, actual_surface_points, clip_surface_points
from utils.formatting import fmt_number, format_surcharge_value, format_normal_force_values


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(value: str) -> str:
    return _re.sub(r'\s+', ' ', str(value or '')).strip().lower()


def _find_by_name(lst, name: str):
    """Zoek object op exacte naam."""
    return next((x for x in (lst or []) if x.name == name), None)


def y_range_for_project(project: Project) -> tuple[float, float]:
    vals: list[float] = []
    for p in project.profiles:
        for l in p.layers:
            vals.append(l.level)
    for s in project.surfaces:
        for pt in s.points:
            vals.append(pt['y'])
    for w in project.waterlevels:
        vals.append(w.level)
    for sp in project.sheet_piling:
        if sp.top is not None and math.isfinite(sp.top):
            vals.append(sp.top + 2.0)   # ruimte voor gekanteld kop-label
        if math.isfinite(sp.bottom):
            vals.append(sp.bottom - 2.0)  # ruimte voor gekanteld teen-label
    for a in project.anchors:
        vals.append(a.level)
        vals.append(a.level - abs(a.height or 0))
    for rs in project.rigid_supports:
        vals.append(rs.level)
    for ss in project.spring_supports:
        vals.append(ss.level)
    for st in project.struts:
        vals.append(st.level)
    for m in project.moments:
        vals.append(m.level)
    if vals:
        return min(vals) - 1.5, max(vals) + 2.2
    return -10.0, 5.0


def x_range_for_project(project: Project) -> tuple[float, float]:
    dists: list[float] = []
    for s in project.surfaces:
        for pt in s.points:
            if math.isfinite(pt['x']):
                dists.append(abs(pt['x']))
    for a in project.anchors:
        if math.isfinite(a.length):
            dists.append(abs(a.length))
    for st in project.struts:
        if math.isfinite(st.length):
            dists.append(abs(st.length))
    for sl in project.surcharge_loads:
        for pt in sl.points:
            if math.isfinite(pt.get('distance', float('nan'))):
                dists.append(abs(pt['distance']))
    max_dist = max(dists) if dists else 10.0
    if max_dist < 8:
        max_dist = 8.0
    pad = max(1.0, max_dist * 0.12)
    wall_x = project.sheet_piling[0].x if (
        project.sheet_piling and math.isfinite(project.sheet_piling[0].x)
    ) else 0.0
    return wall_x - max_dist - pad, wall_x + max_dist + pad


def get_stage_profile(project: Project, stage: Stage | None, side: str):
    """Selecteer het beste grondprofiel — exacte portage van getStageProfile() JS."""
    wanted = (stage.right_profile if side == 'right' else stage.left_profile) if stage else ''
    wanted_norm = _normalize(wanted)
    profiles = list(project.profiles)
    if not profiles:
        return None

    wall_x = project.sheet_piling[0].x if (
        project.sheet_piling and math.isfinite(project.sheet_piling[0].x)
    ) else 0.0

    side_profiles = sorted(
        [p for p in profiles
         if p.x is not None and math.isfinite(p.x)
         and (p.x >= wall_x if side == 'right' else p.x <= wall_x)],
        key=lambda p: abs(p.x - wall_x)
    )

    exact = [p for p in profiles if p.name == wanted or p.normalized_name == wanted_norm]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        exact_side = sorted(
            [p for p in exact
             if p.x is not None and math.isfinite(p.x)
             and (p.x >= wall_x if side == 'right' else p.x <= wall_x)],
            key=lambda p: abs(p.x - wall_x)
        )
        if exact_side:
            return exact_side[0]
        return exact[-1] if side == 'right' else exact[0]

    if wanted_norm:
        partial = [p for p in profiles
                   if p.normalized_name in wanted_norm or wanted_norm in p.normalized_name]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            partial_side = sorted(
                [p for p in partial
                 if p.x is not None and math.isfinite(p.x)
                 and (p.x >= wall_x if side == 'right' else p.x <= wall_x)],
                key=lambda p: abs(p.x - wall_x)
            )
            if partial_side:
                return partial_side[0]
            return partial[-1] if side == 'right' else partial[0]

    if side_profiles:
        return side_profiles[0]

    ordered = sorted(profiles, key=lambda p: (
        p.x if (p.x is not None and math.isfinite(p.x)) else (p.occurrence or 0)
    ))
    return ordered[-1] if side == 'right' else ordered[0]


# ---------------------------------------------------------------------------
# Bouw grondlaag polygoon — identiek aan buildLayerPolygon() in JS
# ---------------------------------------------------------------------------

def _build_layer_polygon(
    surface_pts: list[dict],
    layer_top: float,
    layer_bottom: float,
) -> list[tuple[float, float]]:
    """Polygoon voor één grondlaag in data-coördinaten."""
    if not surface_pts or len(surface_pts) < 2:
        return []
    x_min = surface_pts[0]['x']
    x_max = surface_pts[-1]['x']
    span = max(1e-6, x_max - x_min)
    n = max(90, min(260, round(span * 16)))
    top_pts: list[tuple[float, float]] = []
    bot_pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        x = x_min + span * i / n
        sy = surface_y_at(surface_pts, x)
        ty = min(sy, layer_top)
        if ty > layer_bottom + 1e-9:
            top_pts.append((x, ty))
            bot_pts.append((x, layer_bottom))
    if len(top_pts) < 2:
        return []
    return top_pts + list(reversed(bot_pts))


# ---------------------------------------------------------------------------
# Teken-helpers op ax (data-coördinaten)
# ---------------------------------------------------------------------------

def _draw_poly(ax: Axes, pts: list[tuple], fc, ec, lw=0.8, clip=True, zorder=2):
    if not pts or len(pts) < 3:
        return
    poly = MplPolygon(pts, closed=True,
                       facecolor=fc if fc else 'none',
                       edgecolor=ec if ec else 'none',
                       linewidth=lw, clip_on=clip, zorder=zorder)
    ax.add_patch(poly)


def _fill_arrows(ax: Axes, surface_pts: list[dict],
                  x1: float, x2: float, height: float,
                  fc='white', ec='#222222', n_arrows: int = 8):
    """Vul een belastingblok met neerwaartse pijlen (uniform/surcharge).
    height > 0 in data-eenheden (meters).
    """
    clipped = clip_surface_points(surface_pts, x1, x2)
    if len(clipped) < 2:
        return
    # Bouw polygoon: boven-lijn + omgekeerde maaiveld-lijn
    top = [(p['x'], p['y'] + height) for p in clipped]
    bot = [(p['x'], p['y']) for p in clipped]
    poly_pts = top + list(reversed(bot))
    _draw_poly(ax, poly_pts, fc='white', ec='#222222', lw=0.8, zorder=4)
    # Pijlen
    x_start, x_end = clipped[0]['x'], clipped[-1]['x']
    span = abs(x_end - x_start)
    if span < 1e-6:
        return
    arrow_xs = [x_start + span * (k + 0.5) / n_arrows for k in range(n_arrows)]
    for ax_x in arrow_xs:
        sy = surface_y_at(clipped, ax_x)
        ty = sy + height
        if ty > sy + 0.05:
            ax.annotate(
                '', xy=(ax_x, sy + 0.02), xytext=(ax_x, ty - 0.02),
                arrowprops=dict(arrowstyle='->', color='#333333', lw=1.0),
                clip_on=True, annotation_clip=True, zorder=5
            )


def _draw_moment_symbol(ax: Axes, x: float, y: float,
                         clockwise: bool, color: str, radius: float):
    """Gebogen pijl voor momentensymbool."""
    if clockwise:
        theta1, theta2 = -99, 99
    else:
        theta1, theta2 = 81, 279
    arc = Arc((x, y), 2 * radius, 2 * radius,
               angle=0, theta1=theta1, theta2=theta2,
               color=color, linewidth=1.8, zorder=7)
    ax.add_patch(arc)
    # pijlpunt
    t = math.radians(theta2 if clockwise else theta1)
    tip_x = x + radius * math.cos(t)
    tip_y = y + radius * math.sin(t)
    tang = t + (math.pi / 2 if clockwise else -math.pi / 2)
    al = radius * 0.4
    ax.annotate('', xy=(tip_x, tip_y),
                 xytext=(tip_x - al * math.cos(tang), tip_y - al * math.sin(tang)),
                 arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
                 clip_on=True, zorder=7)


def _draw_zigzag(ax: Axes, x1: float, x2: float, y: float,
                  amplitude: float, segment: float, color: str):
    length = x2 - x1
    count = max(3, int(abs(length) / segment))
    xs = [x1]
    ys = [y]
    for i in range(1, count + 1):
        t = i / count
        xs.append(x1 + length * t)
        ys.append(y + (amplitude if i % 2 == 0 else -amplitude))
    xs.append(x2)
    ys.append(y)
    ax.plot(xs, ys, color=color, linewidth=1.6, clip_on=True, zorder=6)


def _draw_attachment_label(ax: Axes, level: float, wall_x: float, side: str,
                            fontsize: float = 8.0):
    if not math.isfinite(level):
        return
    ox = -0.25 if side == 'left' else 0.25
    ha = 'right' if side == 'left' else 'left'
    ax.text(wall_x + ox, level, f'({fmt_number(level)})',
            ha=ha, va='center', fontsize=fontsize, color='#1e2a32',
            clip_on=True, zorder=8)


def _draw_maaiveld_symbool(
    ax: Axes,
    x_anker: float,
    y_anker: float,
    extend_dir: float,
    sym_breedte: float,
    schaal: float = 1.0,
    color: str = '#8b7d1a',
    zorder: int = 4,
) -> None:
    """Maaiveld-symbool: zigzag van ▽ en △ driehoeken met analytische inwendige diagonalen.

    ▽ (basis boven): 4 lijnen evenwijdig aan linker zijde → '\\'-richting
    △ (basis onder, niet getekend): 4 lijnen evenwijdig aan linker zijde → '/'-richting

    Parameters
    ----------
    extend_dir
        +1 → rechts van x_anker, -1 → links.
    """
    db = 0.45 * schaal                               # driehoekbreedte geschaald [m]
    n = min(4, max(1, int(sym_breedte / db)))        # max 4 ▽-driehoeken, niet oprekken
    h = db * 0.80                             # hoogte
    yt = y_anker
    yb = y_anker - h
    x_start = x_anker if extend_dir > 0 else x_anker - n * db
    lw = 0.9

    # ── Zigzag-omtrek (alle diagonale zijden, geen horizontale boven/onderlijn) ──
    zx: list[float] = []
    zy: list[float] = []
    for i in range(n):
        zx.append(x_start + i * db)
        zy.append(yt)
        zx.append(x_start + (2 * i + 1) * db / 2)
        zy.append(yb)
    zx.append(x_start + n * db)
    zy.append(yt)
    ax.plot(zx, zy, color=color, linewidth=lw, clip_on=True, zorder=zorder)

    # ── Inwendige diagonalen ▽ (basis boven, \-richting) ──────────────────────
    # Lijn j start op bovenkant: (xl + j*db/5, yt)
    # Eindpunt op rechter zijde (afgeleid via parametrische snijberekening):
    #   x = xl + (j+5)*db/10,  y = yt - (5-j)*h/5
    for i in range(n):
        xl = x_start + i * db
        for j in range(1, 5):
            sx = xl + j * db / 5
            ex = xl + (j + 5) * db / 10
            ey = yt - (5 - j) * h / 5
            ax.plot([sx, ex], [yt, ey], color=color, linewidth=lw,
                    clip_on=True, zorder=zorder)

    # ── Inwendige diagonalen △ (basis onder niet getekend, /-richting) ─────────
    # △ j zit tussen ▽ i en ▽ i+1: xl_u = x_start + (2j+1)*db/2
    # Lijn k start op onderkant: (xl_u + k*db/5, yb)
    # Eindpunt op rechter zijde:
    #   x = xl_u + (k+5)*db/10,  y = yb + (5-k)*h/5
    for j in range(n - 1):
        xl_u = x_start + (2 * j + 1) * db / 2
        for k in range(1, 5):
            sx = xl_u + k * db / 5
            ex = xl_u + (k + 5) * db / 10
            ey = yb + (5 - k) * h / 5
            ax.plot([sx, ex], [yb, ey], color=color, linewidth=lw,
                    clip_on=True, zorder=zorder)


# ---------------------------------------------------------------------------
# Hoofd-renderer
# ---------------------------------------------------------------------------

class SectionRenderer(BaseRenderer):
    """Damwand doorsnede-visualisatie."""

    def render(
        self,
        ax: Axes,
        project: Project,
        stage: Stage | None,
        settings: RenderSettings,
        viewport: ViewportSettings,
    ) -> None:
        ax.cla()
        ax.set_facecolor('#ecebd8')  # luchtkleur als achtergrond

        # ── Bereik ──────────────────────────────────────────────────
        if viewport.auto:
            y_min, y_max = y_range_for_project(project)
            x_min, x_max = x_range_for_project(project)
        else:
            y_min, y_max = viewport.y_min, viewport.y_max
            x_min, x_max = viewport.x_min, viewport.x_max

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal', adjustable='box')

        # ── Damwanddata ──────────────────────────────────────────────
        wall_segs = sorted(
            project.sheet_piling,
            key=lambda s: (s.segment_bottom if s.segment_bottom is not None
                           else (s.bottom if math.isfinite(s.bottom) else -math.inf)),
            reverse=True
        )
        wall = wall_segs[0] if wall_segs else None
        wall_x = wall.x if (wall and math.isfinite(wall.x)) else 0.0
        wall_top = (
            max(s.segment_top if s.segment_top is not None else
                (s.top if s.top is not None and math.isfinite(s.top) else y_min)
                for s in wall_segs)
            if wall_segs else 0.0
        )
        wall_bot = (
            min(s.segment_bottom if s.segment_bottom is not None else
                (s.bottom if math.isfinite(s.bottom) else y_min)
                for s in wall_segs)
            if wall_segs else y_min
        )
        wall_max_w = max(
            (s.width if math.isfinite(s.width) else 1.0) for s in wall_segs
        ) if wall_segs else 1.0
        # breedte in data-eenheden: vast ~0.4m zodat het zichtbaar is
        wall_half_w_data = max(0.15, wall_max_w * 0.1)

        # ── Oppervlakken ophalen ─────────────────────────────────────
        left_surf = (_find_by_name(project.surfaces, stage.left_surface)
                      if stage else None) or (project.surfaces[0] if project.surfaces else None)
        right_surf = (_find_by_name(project.surfaces, stage.right_surface)
                       if stage else None) or (
            project.surfaces[1] if len(project.surfaces) > 1
            else project.surfaces[0] if project.surfaces else None
        )
        left_water = (_find_by_name(project.waterlevels, stage.left_water)
                       if stage else None) or (project.waterlevels[0] if project.waterlevels else None)
        right_water = (_find_by_name(project.waterlevels, stage.right_water)
                        if stage else None) or (project.waterlevels[0] if project.waterlevels else None)
        left_prof = get_stage_profile(project, stage, 'left')
        right_prof = get_stage_profile(project, stage, 'right')

        fb_left_y = left_prof.layers[0].level if (left_prof and left_prof.layers) else 0.0
        fb_right_y = right_prof.layers[0].level if (right_prof and right_prof.layers) else 0.0

        left_pts = actual_surface_points(left_surf, 'left', wall_x, x_min, fb_left_y)
        right_pts = actual_surface_points(right_surf, 'right', wall_x, x_max, fb_right_y)
        _left_surf_y  = surface_y_at(left_pts,  wall_x) if left_pts  else fb_left_y
        _right_surf_y = surface_y_at(right_pts, wall_x) if right_pts else fb_right_y

        # ── Rasterlijnen: 1 m hoofdlijnen + 0,1 m hulplijnen ────────
        from matplotlib.ticker import MultipleLocator
        ax.yaxis.set_major_locator(MultipleLocator(1.0))
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.grid(which='major', axis='y', color='#d8dee4', linewidth=0.7, zorder=0)
        ax.grid(which='minor', axis='y', color='#ebebeb', linewidth=0.25, zorder=0)
        ax.tick_params(axis='y', which='minor', left=True, labelleft=False,
                       length=3, width=0.5, color='#aaaaaa')

        # ── Grondlagen ───────────────────────────────────────────────
        def draw_ground(profile, pts: list[dict], side: str):
            if not profile or not profile.layers or not pts:
                return
            x_start = pts[0]['x']
            x_end = pts[-1]['x']
            span = max(1e-6, x_end - x_start)
            n_samples = max(40, min(120, round(span * 10)))

            for i, layer in enumerate(profile.layers):
                layer_top = layer.level
                layer_bot = (profile.layers[i + 1].level
                              if i + 1 < len(profile.layers) else y_min)
                poly = _build_layer_polygon(pts, layer_top, layer_bot)
                if not poly:
                    continue
                fc = color_for_matplotlib(
                    project.soil_color_map.get(layer.material, 'rgb(220,220,220)')
                )
                _draw_poly(ax, poly, fc=fc, ec='none', lw=0, zorder=2)
                # Laaggrens als horizontale lijn, alleen waar maaiveld erboven ligt
                if i > 0 and layer_top > y_min:
                    # Bereken alle x-knikpunten incl. kruisingen met layer_top
                    crit_xs: list[float] = [x_start, x_end]
                    for p in pts:
                        if x_start <= p['x'] <= x_end:
                            crit_xs.append(p['x'])
                    for pi in range(len(pts) - 1):
                        p1, p2 = pts[pi], pts[pi + 1]
                        dy = p2['y'] - p1['y']
                        if abs(dy) > 1e-12:
                            t = (layer_top - p1['y']) / dy
                            if 0 < t < 1:
                                xi = p1['x'] + t * (p2['x'] - p1['x'])
                                if x_start <= xi <= x_end:
                                    crit_xs.append(xi)
                    crit_xs = sorted(set(crit_xs))
                    seg_x0: float | None = None
                    for ci in range(len(crit_xs) - 1):
                        xm = (crit_xs[ci] + crit_xs[ci + 1]) / 2
                        if surface_y_at(pts, xm) >= layer_top - 1e-6:
                            if seg_x0 is None:
                                seg_x0 = crit_xs[ci]
                        else:
                            if seg_x0 is not None:
                                ax.plot([seg_x0, crit_xs[ci]], [layer_top, layer_top],
                                        color='#6c7882', linewidth=0.8,
                                        clip_on=True, zorder=3)
                                seg_x0 = None
                    if seg_x0 is not None:
                        ax.plot([seg_x0, crit_xs[-1]], [layer_top, layer_top],
                                color='#6c7882', linewidth=0.8,
                                clip_on=True, zorder=3)

                # laagnaam op meest zichtbare positie
                best_x, best_mid_y, best_th = None, None, -1.0
                for s in range(n_samples + 1):
                    xi = x_start + span * s / n_samples
                    vis_top = min(layer_top, surface_y_at(pts, xi))
                    th = vis_top - layer_bot
                    if th > best_th:
                        best_th = th
                        best_x = xi
                        best_mid_y = (vis_top + layer_bot) / 2

                if not (best_th > 0.18) or best_mid_y is None:
                    continue
                # Label verankerd aan de buitenrand van het grondvlak, 0.3 m offset
                lx = (x_start + 0.3) if side == 'left' else (x_end - 0.3)
                ha = 'left' if side == 'left' else 'right'
                if y_min + 0.3 < best_mid_y < y_max - 0.3:
                    ax.text(lx, best_mid_y, layer.material,
                            ha=ha, va='center', fontsize=settings.fs_grondlagen,
                            color='#1e2a32', clip_on=True, zorder=3)

        draw_ground(left_prof, left_pts, 'left')
        draw_ground(right_prof, right_pts, 'right')

        # ── Waterarcering (waterpeil boven maaiveld) ─────────────────
        def draw_water_inundation(water, pts: list[dict], x1: float, x2: float) -> None:
            if not water or not math.isfinite(water.level) or not pts:
                return
            wl = water.level
            xs: set[float] = {x1, x2} | {p['x'] for p in pts if x1 <= p['x'] <= x2}
            # Voeg exacte snijpunten toe waar maaiveld de waterlijn kruist
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i + 1]
                if not (x1 <= p1['x'] <= x2 and x1 <= p2['x'] <= x2):
                    continue
                dy = p2['y'] - p1['y']
                if abs(dy) > 1e-12:
                    t = (wl - p1['y']) / dy
                    if 0.0 < t < 1.0:
                        xs.add(p1['x'] + t * (p2['x'] - p1['x']))
            xs_sorted = sorted(xs)
            if not any(surface_y_at(pts, x) < wl - 1e-6 for x in xs_sorted):
                return
            top_pts = [(x, wl) for x in xs_sorted]
            bot_pts = [(x, min(surface_y_at(pts, x), wl)) for x in reversed(xs_sorted)]
            patch = MplPolygon(
                top_pts + bot_pts, closed=True,
                facecolor=(0.55, 0.78, 1.0, 0.18),
                edgecolor=(0.2, 0.5, 0.9, 0.40),
                hatch='//',
                linewidth=0.0,
                clip_on=True, zorder=3,
            )
            ax.add_patch(patch)

        draw_water_inundation(left_water, left_pts, x_min, wall_x)
        draw_water_inundation(right_water, right_pts, wall_x, x_max)

        # ── Maaiveldlijn ─────────────────────────────────────────────
        def draw_surface_line(pts: list[dict]):
            if not pts:
                return
            ax.plot([p['x'] for p in pts], [p['y'] for p in pts],
                    color='#8b7d1a', linewidth=1.7, clip_on=True, zorder=4)

        draw_surface_line(left_pts)
        draw_surface_line(right_pts)

        # Maaiveld-symbolen aan de buitenranden; breedte = buitenste segment tot eerste knikpunt
        # Niet tekenen als het waterpeil aan de betreffende zijde boven het maaiveld uitkomt
        sym_w_fallback = min(2.5, max(0.8, (x_max - x_min) * 0.09))
        if left_pts:
            lw_lv = left_water.level if (left_water and math.isfinite(left_water.level)) else -1e9
            if lw_lv <= left_pts[0]['y']:
                seg_l = (abs(left_pts[1]['x'] - left_pts[0]['x'])
                         if len(left_pts) > 1 else sym_w_fallback)
                _draw_maaiveld_symbool(ax, left_pts[0]['x'], left_pts[0]['y'],
                                        +1.0, seg_l, schaal=settings.maaiveld_schaal)
        if right_pts:
            rw_lv = right_water.level if (right_water and math.isfinite(right_water.level)) else -1e9
            if rw_lv <= right_pts[-1]['y']:
                seg_r = (abs(right_pts[-1]['x'] - right_pts[-2]['x'])
                         if len(right_pts) > 1 else sym_w_fallback)
                _draw_maaiveld_symbool(ax, right_pts[-1]['x'], right_pts[-1]['y'],
                                        -1.0, seg_r, schaal=settings.maaiveld_schaal)

        # Niveaulabels op knikpunten (exacte portage van drawSurfaceLevelLabels)
        def draw_kink_labels(pts: list[dict]):
            if len(pts) < 3:
                return
            for i in range(1, len(pts) - 1):
                pt, prev, nxt = pts[i], pts[i - 1], pts[i + 1]
                dx1 = pt['x'] - prev['x']
                dx2 = nxt['x'] - pt['x']
                sl1 = (pt['y'] - prev['y']) / dx1 if abs(dx1) > 1e-6 else None
                sl2 = (nxt['y'] - pt['y']) / dx2 if abs(dx2) > 1e-6 else None
                is_kink = sl1 is None or sl2 is None or abs(sl1 - sl2) > 1e-6
                if not is_kink:
                    continue
                if y_min + 0.3 < pt['y'] < y_max - 0.3:
                    ax.text(pt['x'], pt['y'] + 0.05,
                            f"({fmt_number(pt['x'])}; {fmt_number(pt['y'])})",
                            ha='center', va='bottom', fontsize=settings.fs_knikpunten,
                            color='#8b7d1a', rotation=90, clip_on=True, zorder=5)

        draw_kink_labels(left_pts)
        draw_kink_labels(right_pts)

        # ── Waterpeilen ──────────────────────────────────────────────
        def draw_water(water, x1: float, x2: float):
            if not water or not math.isfinite(water.level):
                return
            lv = water.level
            span_d = abs(x2 - x1)
            mid_x = (x1 + x2) / 2
            wp_s = settings.waterpeil_schaal
            # Hoofdlijn
            ax.plot([x1, x2], [lv, lv], color='#2d64d8', linewidth=1.8,
                    clip_on=True, zorder=5)
            # Drie korte golftekens: schalfactor op breedte en verticale stap
            for i, hw_frac in enumerate([0.08, 0.05, 0.03]):
                hw = span_d * hw_frac * wp_s
                y_w = lv - (i + 1) * 0.1 * wp_s
                ax.plot([mid_x - hw, mid_x + hw], [y_w, y_w],
                        color='#2d64d8', linewidth=1.0, clip_on=True, zorder=5)
            # Label vlak boven de lijn
            ax.text(mid_x, lv + 0.05,
                    f'{water.name} ({lv:.2f})',
                    ha='center', va='bottom', fontsize=settings.fs_waterpeil,
                    color='#2d64d8', clip_on=True, zorder=6)

        draw_water(left_water, x_min, wall_x)
        draw_water(right_water, wall_x, x_max)

        # ── Actieve elementen ophalen ────────────────────────────────
        def active(lst, names):
            return [_find_by_name(lst, n) for n in (names or []) if _find_by_name(lst, n)]

        act_anchors = active(project.anchors, stage.anchors if stage else [])
        act_struts = active(project.struts, stage.struts if stage else [])
        act_springs = active(project.spring_supports, stage.spring_supports if stage else [])
        act_rigid = active(project.rigid_supports, stage.rigid_supports if stage else [])
        act_uniform = active(project.uniform_loads, stage.uniform_loads if stage else [])
        act_sur_l = active(project.surcharge_loads, stage.surcharge_loads_left if stage else [])
        act_sur_r = active(project.surcharge_loads, stage.surcharge_loads_right if stage else [])
        act_hloads = active(project.horizontal_line_loads, stage.horizontal_line_loads if stage else [])
        act_moments = active(project.moments, stage.moments if stage else [])
        act_nf = active(project.normal_forces, stage.normal_forces if stage else [])

        # ── Uniforme belastingen ─────────────────────────────────────
        y_span = max(1e-6, y_max - y_min)
        for load in act_uniform:
            for value, pts_side, x1d, x2d in [
                (load.left, left_pts, x_min, wall_x - 0.12),
                (load.right, right_pts, wall_x + 0.12, x_max),
            ]:
                if value <= 0:
                    continue
                height = max(0.3, abs(value) * settings.uniform_meters_per_10kpa / 10)
                n_arr = max(1, round(abs(x2d - x1d) / 0.5))
                _fill_arrows(ax, pts_side, x1d, x2d, height,
                              n_arrows=n_arr)
                mid_x = (x1d + x2d) / 2
                sy = surface_y_at(pts_side, mid_x)
                ax.text(mid_x, sy + height + y_span * 0.015,
                        f'{load.name} ({fmt_number(value)} kPa)',
                        ha='center', va='bottom', fontsize=settings.fs_belastingen,
                        color='#111', clip_on=True, zorder=6)

        # ── Surcharge belastingen ────────────────────────────────────
        def draw_surcharge(loads, pts_side: list[dict], side: str):
            for load in loads:
                if not load.points:
                    continue
                sorted_pts = sorted(load.points, key=lambda p: p['distance'])
                top_d: list[tuple] = []
                bot_d: list[tuple] = []
                for pt in sorted_pts:
                    offset = abs(pt['distance'])
                    xd = wall_x - offset if side == 'left' else wall_x + offset
                    sy = surface_y_at(pts_side, xd)
                    height = max(0.3, abs(pt['value']) * settings.uniform_meters_per_10kpa / 10)
                    top_d.append((xd, sy + height))
                    bot_d.append((xd, sy))
                if not top_d:
                    continue
                shape = top_d + list(reversed(bot_d))
                _draw_poly(ax, shape, fc='white', ec='#222222', lw=0.8, zorder=4)
                # pijlen om de 0.5m, hoogte geïnterpoleerd uit top_d/bot_d
                # sorteer op x zodat np.interp correct werkt (ook voor linkerzijde)
                pairs = sorted(zip([p[0] for p in top_d],
                                   [p[1] for p in top_d],
                                   [p[1] for p in bot_d]))
                xs_ref  = [p[0] for p in pairs]
                ys_top  = [p[1] for p in pairs]
                ys_bot  = [p[2] for p in pairs]
                x_start, x_end = xs_ref[0], xs_ref[-1]
                span = x_end - x_start
                n_arr = max(1, round(span / 0.5)) if span > 1e-6 else 1
                for k in range(n_arr):
                    ax_x = x_start + span * (k + 0.5) / n_arr
                    ty = float(np.interp(ax_x, xs_ref, ys_top))
                    by = float(np.interp(ax_x, xs_ref, ys_bot))
                    if ty - by > 0.05:
                        ax.annotate('', xy=(ax_x, by + 0.02), xytext=(ax_x, ty - 0.02),
                                     arrowprops=dict(arrowstyle='->', color='#333', lw=0.9),
                                     clip_on=True, annotation_clip=True, zorder=5)
                lx = sum(x for x, _ in top_d) / len(top_d)
                ly = min(y for _, y in top_d)
                ax.text(lx, ly + y_span * 0.012,
                        f'{load.name} ({format_surcharge_value(load.points)})',
                        ha='center', va='bottom', fontsize=settings.fs_belastingen,
                        color='#111', clip_on=True, zorder=6)

        draw_surcharge(act_sur_l, left_pts, 'left')
        draw_surcharge(act_sur_r, right_pts, 'right')

        # ── Ankers ───────────────────────────────────────────────────
        for a in act_anchors:
            # side=2 → rechts (+1), side=1 → links (-1)  (identiek aan JS)
            side_mult = 1 if a.side == 2 else -1
            angle_deg = abs(a.angle) if math.isfinite(a.angle) else 15.0
            length = a.length if math.isfinite(a.length) else 8.0
            dx = math.cos(math.radians(angle_deg)) * length * side_mult
            dy = -math.sin(math.radians(angle_deg)) * length
            x2, y2 = wall_x + dx, a.level + dy

            ax.plot([wall_x, x2], [a.level, y2],
                    color='#111111', linewidth=2.5, solid_capstyle='round',
                    clip_on=True, zorder=6)

            kranz_h = abs(float(a.height) if math.isfinite(a.height) else 0.0)
            if kranz_h > 0:
                ax.plot([x2, x2], [y2 + kranz_h / 2, y2 - kranz_h / 2],
                        color='#111111', linewidth=2.5, clip_on=True, zorder=6)
            else:
                # Groutlichaam: twee parallelle lijnen
                grout_len = min(length * 0.25, 3.0)
                ux = dx / length if length > 0 else side_mult
                uy = dy / length if length > 0 else 0.0
                nx, ny = -uy, ux
                for sign in [-1, 1]:
                    ox, oy = nx * 0.25 * sign, ny * 0.25 * sign
                    gx1 = x2 - ux * grout_len
                    gy1 = y2 - uy * grout_len
                    ax.plot([gx1 + ox, x2 + ox], [gy1 + oy, y2 + oy],
                            color='#111111', linewidth=1.8, clip_on=True, zorder=6)

            ha = 'right' if dx < 0 else 'left'
            ax.text(x2 + (-0.2 if dx < 0 else 0.2), y2, a.name,
                    ha=ha, va='center', fontsize=settings.fs_constructie,
                    color='#111', clip_on=True, zorder=7)
            _draw_attachment_label(ax, a.level, wall_x,
                                    'right' if side_mult < 0 else 'left',
                                    settings.fs_constructie)

        # ── Stempels ─────────────────────────────────────────────────
        for st in act_struts:
            side_mult = -1 if st.side == 1 else 1
            angle_deg = abs(st.angle) if math.isfinite(st.angle) else 10.0
            length = st.length if math.isfinite(st.length) else 8.0
            dx = math.cos(math.radians(angle_deg)) * length * side_mult
            dy = math.sin(math.radians(angle_deg)) * length * (1 if side_mult > 0 else -1)
            x2, y2 = wall_x + dx, st.level + dy
            ax.plot([wall_x, x2], [st.level, y2],
                    color='#666666', linewidth=7.0, solid_capstyle='round',
                    clip_on=True, zorder=5)
            ax.plot([wall_x, x2], [st.level, y2],
                    color='#111111', linewidth=1.2, clip_on=True, zorder=6)
            ha = 'right' if dx < 0 else 'left'
            ax.text(x2 + (-0.2 if dx < 0 else 0.2), y2, st.name,
                    ha=ha, va='center', fontsize=settings.fs_constructie,
                    color='#111', clip_on=True, zorder=7)
            _draw_attachment_label(ax, st.level, wall_x,
                                    'right' if side_mult < 0 else 'left',
                                    settings.fs_constructie)

        # ── Veersteun ─────────────────────────────────────────────────
        # Symbool (links van de wand): wand ——[■]——/\/\/——|
        for ss in act_springs:
            u = max(0.25, abs(y_max - y_min) * 0.022) * 2 / 3
            L = u * 5.5          # totale symboollengte
            sq = u * 0.7         # zijde van het vierkantje
            amp = u * 0.35       # zigzag-amplitude
            seg = u * 0.5        # zigzag-segmentlengte

            x_wall = wall_x      # aanhechtpunt aan de wand
            x_sq_r = x_wall - u * 0.5          # rechts van vierkant
            x_sq_l = x_sq_r - sq               # links van vierkant
            x_zz_end = x_sq_l - u * 0.3        # eind zigzag / begin vierkant
            x_zz_start = x_wall - L + u * 0.6  # begin zigzag
            x_bar = x_zz_start - u * 0.3       # eindstaaf x-positie

            # Lijn wand → vierkant (rechts)
            ax.plot([x_wall, x_sq_r], [ss.level, ss.level],
                    color='#111', linewidth=1.6, clip_on=True, zorder=6)
            # Vierkant (box)
            rect = Rectangle((x_sq_l, ss.level - sq / 2), sq, sq,
                               edgecolor='#111', facecolor='none',
                               linewidth=1.4, clip_on=True, zorder=6)
            ax.add_patch(rect)
            # Lijn vierkant → zigzag
            ax.plot([x_sq_l, x_zz_end], [ss.level, ss.level],
                    color='#111', linewidth=1.6, clip_on=True, zorder=6)
            # Zigzag (veer)
            _draw_zigzag(ax, x_zz_end, x_zz_start, ss.level, amp, seg, '#111')
            # Eindstaaf (verticale balk)
            ax.plot([x_bar, x_bar], [ss.level - u * 0.6, ss.level + u * 0.6],
                    color='#111', linewidth=2.0, clip_on=True, zorder=6)

            ax.text(x_bar - u * 0.3, ss.level, ss.name,
                    ha='right', va='center', fontsize=settings.fs_constructie,
                    color='#111', clip_on=True, zorder=7)
            _draw_attachment_label(ax, ss.level, wall_x, 'right',
                                    settings.fs_constructie)

        # ── Rigide steun ──────────────────────────────────────────────
        # rotation only     : gecentreerd OP de wand     ——[≡]——
        # translation only  : naar zijde laagste maaiveld  ——|
        # translation + rot : rot-box op wand + tr-staaf naar lage zijde

        # Richting voor translation: kant met laagste maaiveld
        left_surf_y, right_surf_y = _left_surf_y, _right_surf_y
        tr_dir = -1.0 if left_surf_y < right_surf_y else 1.0  # -1=links, +1=rechts

        for rs in act_rigid:
            u       = max(0.25, abs(y_max - y_min) * 0.022)
            sc_L    = u * 4.0 / 3       # totaallengte translation-arm
            sc_sq   = u * 0.7 * 2 / 3   # vierkant-zijde rotation
            sc_barh = u * 0.7 * 2 / 3   # halve hoogte eindstaaf
            # Symbolen starten aan de buitenrand van de damwand
            wall_edge_tr  = wall_x + tr_dir * wall_half_w_data
            wall_edge_l   = wall_x - wall_half_w_data
            wall_edge_r   = wall_x + wall_half_w_data

            has_tr  = bool(rs.tr_stiff)
            has_rot = bool(rs.rot_stiff)

            def _draw_rot_box(level=rs.level):
                """Vier losse buitenlijnen, gecentreerd op wall_x (zorder=9).
                   Armpjes lopen alleen tot de buitenrand van de damwand."""
                bx_l = wall_x - sc_sq / 2
                bx_r = wall_x + sc_sq / 2
                bx_t = level + sc_sq / 2
                bx_b = level - sc_sq / 2
                kw = dict(color='#111', linewidth=1.4, clip_on=True, zorder=9)
                ax.plot([bx_l, bx_r], [bx_t, bx_t], **kw)  # boven
                ax.plot([bx_l, bx_r], [bx_b, bx_b], **kw)  # onder
                ax.plot([bx_l, bx_l], [bx_b, bx_t], **kw)  # links
                ax.plot([bx_r, bx_r], [bx_b, bx_t], **kw)  # rechts
                # Zijlijn links: van box-rand tot wand-buitenrand (niet voorbij)
                if bx_l > wall_edge_l:
                    ax.plot([wall_edge_l, bx_l], [level, level], **kw)
                # Zijlijn rechts: van box-rand tot wand-buitenrand (niet voorbij)
                if bx_r < wall_edge_r:
                    ax.plot([bx_r, wall_edge_r], [level, level], **kw)

            if has_tr and has_rot:
                # Rotatie-box op wand; translation-staaf naar lage zijde
                _draw_rot_box()
                x_bar = wall_edge_tr + tr_dir * sc_L
                ax.plot([wall_edge_tr, x_bar],
                        [rs.level, rs.level],
                        color='#111', linewidth=1.6, clip_on=True, zorder=9)
                ax.plot([x_bar, x_bar],
                        [rs.level - sc_barh, rs.level + sc_barh],
                        color='#111', linewidth=2.0, clip_on=True, zorder=9)
                label_x  = x_bar
                label_ha = 'right' if tr_dir < 0 else 'left'

            elif has_tr:
                # Translation-only: lijn + staaf, startend aan wand-rand
                x_bar = wall_edge_tr + tr_dir * sc_L
                ax.plot([wall_edge_tr, x_bar], [rs.level, rs.level],
                        color='#111', linewidth=1.6, clip_on=True, zorder=9)
                ax.plot([x_bar, x_bar],
                        [rs.level - sc_barh, rs.level + sc_barh],
                        color='#111', linewidth=2.0, clip_on=True, zorder=9)
                label_x  = x_bar
                label_ha = 'right' if tr_dir < 0 else 'left'

            else:
                # Rotation-only: alleen de box (zijlijnen al in _draw_rot_box)
                _draw_rot_box()
                label_x  = wall_edge_r
                label_ha = 'left'

            sign = 1 if label_ha == 'left' else -1
            ax.text(label_x + sign * u * 0.2, rs.level, rs.name,
                    ha=label_ha, va='center', fontsize=settings.fs_constructie,
                    color='#111', clip_on=True, zorder=7)
            # Hoogtelabel: tr/gecombineerd → hoogste maaiveld; rot-only → laagste
            if has_rot and not has_tr:
                level_label_side = 'right' if tr_dir < 0 else 'left'
            else:
                level_label_side = 'right' if tr_dir < 0 else 'left'
            _draw_attachment_label(ax, rs.level, wall_x, level_label_side,
                                    settings.fs_constructie)

        # ── Horizontale lijnlasten ────────────────────────────────────
        for hl in act_hloads:
            value = float(hl.value) or 0.0
            stem = settings.hload_scale
            to_wall = value >= 0  # positief = naar de wand (van links)
            if to_wall:
                start_x = wall_x - stem
                ax.annotate('', xy=(wall_x, hl.level), xytext=(start_x, hl.level),
                             arrowprops=dict(arrowstyle='->', color='#111', lw=2.2),
                             clip_on=True, zorder=6)
                ax.text(start_x - 0.1, hl.level,
                        f'{hl.name} ({fmt_number(value)} kN/m)',
                        ha='right', va='center', fontsize=settings.fs_belastingen,
                        color='#111', clip_on=True, zorder=7)
            else:
                start_x = wall_x + stem
                ax.annotate('', xy=(wall_x, hl.level), xytext=(start_x, hl.level),
                             arrowprops=dict(arrowstyle='->', color='#111', lw=2.2),
                             clip_on=True, zorder=6)
                ax.text(start_x + 0.1, hl.level,
                        f'{hl.name} ({fmt_number(value)} kN/m)',
                        ha='left', va='center', fontsize=settings.fs_belastingen,
                        color='#111', clip_on=True, zorder=7)

        # ── Momenten ─────────────────────────────────────────────────
        for m_obj in act_moments:
            value = float(m_obj.value) or 0.0
            clockwise = value > 0
            radius = max(settings.moment_radius_meters * 0.5, y_span * 0.04)
            _draw_moment_symbol(ax, wall_x + wall_half_w_data, m_obj.level,
                                 clockwise, '#111', radius)
            lx_m = wall_x + wall_half_w_data + radius + 0.1
            ax.text(lx_m, m_obj.level,
                    f'{m_obj.name} ({fmt_number(value)} kNm/m)',
                    ha='left', va='center', fontsize=settings.fs_belastingen,
                    color='#111', clip_on=True, zorder=7)

        # ── Normaalkrachten ───────────────────────────────────────────
        if act_nf:
            wall_top_nf = (project.sheet_piling[0].top
                            if project.sheet_piling and project.sheet_piling[0].top is not None
                            else 0.0)
            wall_bot_nf = (project.sheet_piling[0].bottom
                            if project.sheet_piling and math.isfinite(project.sheet_piling[0].bottom)
                            else y_min)
            ref = {
                'top': wall_top_nf,
                'sl': surface_y_at(left_pts, wall_x),
                'sr': surface_y_at(right_pts, wall_x),
                'bot': wall_bot_nf,
            }
            w_scale = y_span * settings.normal_meters_per_10knm / 10.0 * 0.15

            mid_y_nf = (ref['top'] + ref['bot']) / 2
            nf_labels: list[tuple[float, str, str]] = []
            for nf in act_nf:
                refs = [
                    (ref['top'], float(nf.top) if nf.top is not None else 0.0),
                    (ref['sl'], float(nf.surface_left) if nf.surface_left is not None else 0.0),
                    (ref['sr'], float(nf.surface_right) if nf.surface_right is not None else 0.0),
                    (ref['bot'], float(nf.bottom) if nf.bottom is not None else 0.0),
                ]
                refs = [(y, v) for y, v in refs if math.isfinite(y)]
                if len(refs) < 2:
                    continue
                for i in range(len(refs) - 1):
                    ya, va_v = refs[i]
                    yb, vb = refs[i + 1]
                    if abs(va_v) < 1e-9 and abs(vb) < 1e-9:
                        continue
                    if va_v == 0 or vb == 0 or (va_v > 0) == (vb > 0):
                        pts_nf = [
                            (wall_x, ya),
                            (wall_x + va_v * w_scale, ya),
                            (wall_x + vb * w_scale, yb),
                            (wall_x, yb),
                        ]
                        _draw_poly(ax, pts_nf, fc='rgba(200,200,255,0.3)' if False
                                   else (0.8, 0.8, 1.0, 0.5),
                                   ec='#333', lw=0.8, zorder=4)
                    else:
                        t = abs(va_v) / (abs(va_v) + abs(vb))
                        y_zero = ya + (yb - ya) * t
                        for poly_nf in [
                            [(wall_x, ya), (wall_x + va_v * w_scale, ya), (wall_x, y_zero)],
                            [(wall_x, y_zero), (wall_x + vb * w_scale, yb), (wall_x, yb)],
                        ]:
                            _draw_poly(ax, poly_nf, fc=(0.8, 0.8, 1.0, 0.5),
                                        ec='#333', lw=0.8, zorder=4)

                vals = [v for _, v in refs]
                avg = sum(vals) / len(vals)
                max_abs = max(abs(v) for v in vals)
                ha_nf = 'right' if avg < 0 else 'left'
                lx_nf = wall_x + (-(max_abs * w_scale + 0.3)
                                    if avg < 0 else (max_abs * w_scale + 0.3))
                nf_labels.append((lx_nf, ha_nf, f'{nf.name} ({format_normal_force_values(nf)})'))

            # Labels gestapeld plaatsen zodat ze niet overlappen
            line_h = y_span * 0.04
            n_lbl = len(nf_labels)
            for idx, (lx_nf, ha_nf, lbl_txt) in enumerate(nf_labels):
                y_lbl = mid_y_nf + (idx - (n_lbl - 1) / 2) * line_h
                ax.text(lx_nf, y_lbl, lbl_txt,
                        ha=ha_nf, va='center', fontsize=settings.fs_belastingen,
                        color='#111', clip_on=True, zorder=7)

        # ── Damwand ───────────────────────────────────────────────────
        for seg in wall_segs:
            seg_top = (seg.segment_top if seg.segment_top is not None
                       else (seg.top if seg.top is not None and math.isfinite(seg.top) else wall_top))
            seg_bot = (seg.segment_bottom if seg.segment_bottom is not None
                       else (seg.bottom if math.isfinite(seg.bottom) else wall_bot))
            seg_w_frac = ((seg.width if math.isfinite(seg.width) else wall_max_w)
                           / max(1e-6, wall_max_w))
            seg_half_w = wall_half_w_data * seg_w_frac

            name_lc = str(seg.name or '').lower()
            has_concrete = 'beton' in name_lc or 'concrete' in name_lc
            fill_c = (
                ('#ADAAA9' if seg is wall_segs[0] else '#969696')
                if len(wall_segs) > 1
                else ('#ADAAA9' if has_concrete else '#BE822B')
            )
            rect = Rectangle(
                (wall_x - seg_half_w, seg_bot), 2 * seg_half_w, seg_top - seg_bot,
                facecolor=fill_c, edgecolor='#202428', linewidth=1.2,
                clip_on=True, zorder=6
            )
            ax.add_patch(rect)
            if len(wall_segs) > 1 and seg.name:
                ax.text(wall_x + seg_half_w + 0.1, (seg_top + seg_bot) / 2,
                        seg.name, ha='left', va='center',
                        fontsize=settings.fs_damwand,
                        color='#1e2a32', clip_on=True, zorder=7)
            elif len(wall_segs) == 1 and seg.name and math.isfinite(wall_top):
                rechts_lager = _right_surf_y < _left_surf_y
                rot = 45 if rechts_lager else -45
                ox = 0.2 if rechts_lager else -0.2
                ha = 'left' if rechts_lager else 'right'
                ax.text(wall_x + ox, wall_top, seg.name,
                        ha=ha, va='bottom', rotation=rot,
                        fontsize=settings.fs_damwand,
                        color='#1e2a32', clip_on=True, zorder=7)

        if math.isfinite(wall_top):
            ax.text(wall_x, wall_top + 0.1,
                    f'Kop ({fmt_number(wall_top)})',
                    ha='center', va='bottom', rotation=90,
                    fontsize=settings.fs_damwand,
                    color='#1e2a32', clip_on=True, zorder=7)
        if math.isfinite(wall_bot):
            ax.text(wall_x, wall_bot - 0.1,
                    f'Teen ({fmt_number(wall_bot)})',
                    ha='center', va='top', rotation=90,
                    fontsize=settings.fs_damwand,
                    color='#1e2a32', clip_on=True, zorder=7)

        # ── Assen ─────────────────────────────────────────────────────
        ax.set_ylabel('Niveau [m NAP]', fontsize=settings.fs_assen)
        ax.set_xlabel('x [m]', fontsize=settings.fs_assen)
        ax.tick_params(axis='both', labelsize=settings.fs_assen)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        proj_name = project.project_name
        phase_name = stage.name if stage else '-'
        ax.set_title(f'{proj_name}  –  Fase: {phase_name}',
                      fontsize=settings.fs_titel, fontweight='bold', pad=10)
        ax.grid(False)
