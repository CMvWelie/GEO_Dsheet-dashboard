"""Matplotlib-tekenhulpfuncties voor de D-Sheet renderer."""

from __future__ import annotations
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


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
