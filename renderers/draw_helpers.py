"""Matplotlib-tekenhulpfuncties voor de D-Sheet renderer."""

from __future__ import annotations
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Arc

from utils.color_utils import color_for_matplotlib


def draw_polygon_on_ax(
    ax: Axes,
    points: list[tuple[float, float]],
    face_color=None,
    edge_color=None,
    line_width: float = 1.0,
    alpha: float = 1.0,
    clip_on: bool = True,
) -> None:
    """Teken een gevuld polygoon op een matplotlib-assen.

    Parameters
    ----------
    ax:         Matplotlib Axes.
    points:     Lijst van (x, y) tuples in data-coördinaten.
    face_color: Vulkleur (None = transparant).
    edge_color: Randkleur (None = geen rand).
    line_width: Lijndikte.
    alpha:      Transparantie (0-1).
    clip_on:    Begrens tekenen tot het axes-gebied.
    """
    if not points or len(points) < 3:
        return
    xs, ys = zip(*points)
    poly = plt.Polygon(
        list(zip(xs, ys)),
        closed=True,
        facecolor=face_color if face_color is not None else 'none',
        edgecolor=edge_color if edge_color is not None else 'none',
        linewidth=line_width,
        alpha=alpha,
        clip_on=clip_on,
    )
    ax.add_patch(poly)


def fill_with_vertical_hatch(
    ax: Axes,
    points: list[tuple[float, float]],
    face_color=None,
    edge_color: str = '#333333',
    spacing: float = 0.3,
    clip_on: bool = True,
) -> None:
    """Vul een polygoon met verticale arceerlijnen (voor grondsoorten).

    Parameters
    ----------
    ax:         Matplotlib Axes.
    points:     Polygoon in data-coördinaten.
    face_color: Achtergrondkleur.
    edge_color: Kleur van de arceerlijnen.
    spacing:    Afstand tussen arceerlijnen in data-eenheden.
    clip_on:    Begrens tekenen tot het axes-gebied.
    """
    if not points or len(points) < 3:
        return
    draw_polygon_on_ax(ax, points, face_color=face_color, edge_color=edge_color,
                        line_width=0.8, clip_on=clip_on)
    xs, ys = zip(*points)
    x_min, x_max = min(xs), max(xs)
    x = x_min
    while x <= x_max + spacing:
        ax.plot([x, x], [min(ys) - 1, max(ys) + 1],
                color=edge_color, linewidth=0.7, clip_on=clip_on)
        x += spacing


def fill_with_surface_aligned_arrows(
    ax: Axes,
    top_pts: list[tuple[float, float]],
    bottom_pts: list[tuple[float, float]],
    face_color=None,
    edge_color: str = '#222222',
    spacing: float = 0.5,
    clip_on: bool = True,
) -> None:
    """Vul een belastingblok met neerwaartse pijlen langs het maaiveld.

    Parameters
    ----------
    ax:          Matplotlib Axes.
    top_pts:     Bovenpunten van het belastingblok (data-coördinaten).
    bottom_pts:  Onderpunten (maaiveldlijn).
    face_color:  Achtergrondkleur van het blok.
    edge_color:  Kleur van de pijlen.
    spacing:     Horizontale afstand tussen pijlen in data-eenheden.
    clip_on:     Begrens tekenen tot het axes-gebied.
    """
    if not top_pts or not bottom_pts:
        return
    all_pts = list(top_pts) + list(reversed(bottom_pts))
    draw_polygon_on_ax(ax, all_pts, face_color=face_color or 'white',
                        edge_color=edge_color, line_width=0.8, alpha=0.85, clip_on=clip_on)

    def interp_y(pts: list[tuple[float, float]], x: float) -> float:
        if len(pts) == 1:
            return pts[0][1]
        for i in range(len(pts) - 1):
            ax_x, ax_y = pts[i]
            bx, by = pts[i + 1]
            mn = min(ax_x, bx)
            mx = max(ax_x, bx)
            if mn - 1e-6 <= x <= mx + 1e-6:
                dx = bx - ax_x
                if abs(dx) < 1e-9:
                    return ax_y
                return ax_y + (x - ax_x) / dx * (by - ax_y)
        return pts[-1][1] if x > pts[-1][0] else pts[0][1]

    if len(bottom_pts) >= 2:
        x_start = bottom_pts[0][0]
        x_end = bottom_pts[-1][0]
        n_arrows = max(1, int(abs(x_end - x_start) / spacing))
        for k in range(n_arrows + 1):
            t = (k + 0.5) / (n_arrows + 1)
            bx = x_start + (x_end - x_start) * t
            by = interp_y(list(bottom_pts), bx)
            ty = interp_y(list(top_pts), bx)
            arrow_len = by - ty
            if abs(arrow_len) > 1e-6:
                ax.annotate(
                    '', xy=(bx, by), xytext=(bx, ty),
                    arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.0),
                    clip_on=clip_on
                )


def fill_with_diagonal_hatch(
    ax: Axes,
    points: list[tuple[float, float]],
    face_color: str = 'white',
    edge_color: str = '#222222',
    spacing: float = 0.3,
    alpha: float = 0.7,
    clip_on: bool = True,
) -> None:
    """Vul een polygoon met diagonale arceerlijnen (voor normaalkrachten).

    Parameters
    ----------
    ax:         Matplotlib Axes.
    points:     Polygoon in data-coördinaten.
    face_color: Achtergrondkleur.
    edge_color: Kleur van de diagonale lijnen.
    spacing:    Afstand tussen lijnen.
    alpha:      Transparantie.
    clip_on:    Begrens tekenen tot het axes-gebied.
    """
    if not points or len(points) < 3:
        return
    draw_polygon_on_ax(ax, points, face_color=face_color, edge_color=edge_color,
                        line_width=0.8, alpha=alpha, clip_on=clip_on)
    xs, ys = zip(*points)
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    span = (y_max - y_min) + 2
    x = x_min - span
    while x <= x_max + span:
        ax.plot([x, x + span], [y_max + 1, y_min - 1],
                color=edge_color, linewidth=0.7, clip_on=clip_on)
        x += spacing


def draw_moment_symbol(
    ax: Axes,
    x: float,
    y: float,
    clockwise: bool = True,
    color: str = '#111111',
    radius: float = 0.8,
) -> None:
    """Teken een gebogen pijl als momentensymbool.

    Parameters
    ----------
    ax:        Matplotlib Axes.
    x, y:      Middelpunt in data-coördinaten.
    clockwise: Richting van het moment.
    color:     Kleur van het symbool.
    radius:    Straal van de boog in data-eenheden.
    """
    if clockwise:
        theta1, theta2 = -100, 100
    else:
        theta1, theta2 = 80, 280

    arc = Arc(
        (x, y), 2 * radius, 2 * radius,
        angle=0, theta1=theta1, theta2=theta2,
        color=color, linewidth=1.8
    )
    ax.add_patch(arc)

    # Pijlpunt
    angle_rad = math.radians(theta2 if clockwise else theta1)
    tip_x = x + radius * math.cos(angle_rad)
    tip_y = y + radius * math.sin(angle_rad)
    tangent = angle_rad + (math.pi / 2 if clockwise else -math.pi / 2)
    spread = 0.45
    arrow_len = radius * 0.35
    ax.annotate(
        '', xy=(tip_x, tip_y),
        xytext=(
            tip_x - arrow_len * math.cos(tangent),
            tip_y - arrow_len * math.sin(tangent)
        ),
        arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
        clip_on=True,
    )


def draw_zigzag_line(
    ax: Axes,
    x1: float,
    x2: float,
    y: float,
    amplitude: float = 0.12,
    segment: float = 0.2,
    color: str = '#111111',
    linewidth: float = 1.6,
) -> None:
    """Teken een zigzag-lijn (voor veersteun-symbolen).

    Parameters
    ----------
    ax:        Matplotlib Axes.
    x1, x2:   Begin- en eindpunt in data-x.
    y:         Hoogte in data-y.
    amplitude: Uitwijking van de zigzag.
    segment:   Lengte van elk segment.
    color:     Lijnkleur.
    linewidth: Lijndikte.
    """
    length = x2 - x1
    count = max(3, int(abs(length) / segment))
    xs = [x1]
    ys = [y]
    for i in range(1, count + 1):
        t = i / count
        xi = x1 + length * t
        yi = y + (amplitude if i % 2 == 0 else -amplitude)
        xs.append(xi)
        ys.append(yi)
    xs.append(x2)
    ys.append(y)
    ax.plot(xs, ys, color=color, linewidth=linewidth, clip_on=True)
