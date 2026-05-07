"""Geometrie-hulpfuncties: interpolatie, oppervlak-queries."""

from __future__ import annotations
import math


def surface_y_at(points: list[dict], x: float) -> float:
    """Lineaire interpolatie van de hoogte y op positie x langs een oppervlak.

    Parameters
    ----------
    points: Lijst van dicts met 'x' en 'y' sleutels, gesorteerd op x.
    x:      Horizontale coördinaat waarvoor y bepaald wordt.

    Returns
    -------
    float  Geïnterpoleerde of geëxtrapoleerde y-waarde.
    """
    pts = sorted(
        [p for p in (points or []) if math.isfinite(p['x']) and math.isfinite(p['y'])],
        key=lambda p: p['x']
    )
    if not pts:
        return 0.0
    if len(pts) == 1:
        return pts[0]['y']
    if x <= pts[0]['x']:
        return pts[0]['y']
    if x >= pts[-1]['x']:
        return pts[-1]['y']
    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i + 1]
        if p1['x'] <= x <= p2['x']:
            dx = p2['x'] - p1['x']
            if abs(dx) < 1e-12:
                return p2['y']
            t = (x - p1['x']) / dx
            return p1['y'] + t * (p2['y'] - p1['y'])
    return pts[-1]['y']


def clip_surface_points(points: list[dict], x_start: float, x_end: float) -> list[dict]:
    """Knip een oppervlakpuntreeks bij op het interval [x_start, x_end].

    Voegt interpolatiepunten toe op de grenzen zodat de lijn
    precies begint en eindigt op x_start en x_end.

    Parameters
    ----------
    points:  Lijst van {'x', 'y'} dicts.
    x_start: Linker grens.
    x_end:   Rechter grens.

    Returns
    -------
    list[dict]  Geknipt en gesorteerd puntenstel.
    """
    pts = sorted(
        [p for p in (points or []) if math.isfinite(p['x']) and math.isfinite(p['y'])],
        key=lambda p: p['x']
    )
    if not pts:
        return []
    x1 = min(x_start, x_end)
    x2 = max(x_start, x_end)
    out = [{'x': x1, 'y': surface_y_at(pts, x1)}]
    for pt in pts:
        if x1 + 1e-9 < pt['x'] < x2 - 1e-9:
            out.append({'x': pt['x'], 'y': pt['y']})
    out.append({'x': x2, 'y': surface_y_at(pts, x2)})
    return sorted(out, key=lambda p: p['x'])


def actual_surface_points(
    surface,
    side: str,
    wall_x: float,
    edge_x: float,
    fallback_y: float
) -> list[dict]:
    """Zet een Surface-object om naar absolute coördinaten voor rendering.

    D-Sheet slaat oppervlakpunten op als afstand tot de wand; deze functie
    converteert naar absolute x-coördinaten en voegt randpunten toe.

    Parameters
    ----------
    surface:    Surface dataclass-object (mag None zijn).
    side:       'left' of 'right'.
    wall_x:     Absolute x-positie van de damwand.
    edge_x:     Rand van het viewport (xMin of xMax).
    fallback_y: Hoogte als er geen punten zijn.

    Returns
    -------
    list[dict]  Gesorteerde lijst van {'x', 'y'} punten in absolute coördinaten.
    """
    raw_points = getattr(surface, 'points', []) or []
    pts = [
        {
            'x': (wall_x - p['x']) if side == 'left' else (wall_x + p['x']),
            'y': float(p['y'])
        }
        for p in raw_points
        if math.isfinite(p.get('x', float('nan'))) and math.isfinite(p.get('y', float('nan')))
    ]
    pts.sort(key=lambda p: p['x'])

    if not pts:
        pts = sorted([{'x': edge_x, 'y': fallback_y}, {'x': wall_x, 'y': fallback_y}],
                     key=lambda p: p['x'])

    start_y = surface_y_at(pts, edge_x)
    end_y = surface_y_at(pts, wall_x)
    pts.append({'x': edge_x, 'y': start_y})
    pts.append({'x': wall_x, 'y': end_y})

    x_min = min(edge_x, wall_x)
    x_max = max(edge_x, wall_x)
    pts = [p for p in pts if x_min - 1e-6 <= p['x'] <= x_max + 1e-6]
    pts.sort(key=lambda p: p['x'])

    # Verwijder duplicaten op x
    out: list[dict] = []
    for pt in pts:
        if out and abs(out[-1]['x'] - pt['x']) < 1e-9:
            out[-1] = pt
        else:
            out.append(pt)
    return out


def build_layer_polygons(
    points: list[dict],
    layer_top: float,
    layer_bottom: float,
) -> list[list[tuple[float, float]]]:
    """Bouw polygonen voor één grondlaag, gesplitst bij openingen in het oppervlak.

    Wanneer het oppervlak daalt tot onder ``layer_bottom`` en later weer stijgt,
    ontstaan meerdere losse polygonen. Zonder splitsing zou één polygoon een
    degenerate horizontale brug bevatten op y = layer_bottom.

    Parameters
    ----------
    points:       Oppervlakpunten als {'x', 'y'} dicts.
    layer_top:    Bovenzijde van de laag in m NAP.
    layer_bottom: Onderzijde van de laag in m NAP.

    Returns
    -------
    list[list[tuple[float,float]]]  Lijst van gesloten polygonen als (x, y) tuples.
    """
    if not points or len(points) < 2:
        return []
    x_min = points[0]['x']
    x_max = points[-1]['x']
    span = max(1e-6, x_max - x_min)
    sample_count = max(90, min(260, round(span * 16)))

    polygons: list[list[tuple[float, float]]] = []
    seg_top: list[tuple[float, float]] = []

    for i in range(sample_count + 1):
        x = x_min + span * i / sample_count
        surface_y = surface_y_at(points, x)
        top_y = min(surface_y, layer_top)
        if top_y > layer_bottom + 1e-9:
            seg_top.append((x, top_y))
        else:
            if len(seg_top) >= 2:
                bot = [(xt, layer_bottom) for xt, _ in seg_top]
                polygons.append(seg_top + list(reversed(bot)))
            seg_top = []

    if len(seg_top) >= 2:
        bot = [(xt, layer_bottom) for xt, _ in seg_top]
        polygons.append(seg_top + list(reversed(bot)))

    return polygons


def build_layer_polygon(
    points: list[dict],
    layer_top: float,
    layer_bottom: float,
) -> list[tuple[float, float]]:
    """Bouw één polygoon voor één grondlaag (enkelvoudige terugvalvariant).

    Parameters
    ----------
    points:       Oppervlakpunten als {'x', 'y'} dicts.
    layer_top:    Bovenzijde van de laag in m NAP.
    layer_bottom: Onderzijde van de laag in m NAP.

    Returns
    -------
    list[tuple[float,float]]  Eerste polygoon als (x, y) tuples, of lege lijst.
    """
    polys = build_layer_polygons(points, layer_top, layer_bottom)
    return polys[0] if polys else []
