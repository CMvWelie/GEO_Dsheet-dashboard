"""Opmaakhulpfuncties voor getallen en waarden."""

from __future__ import annotations
import math


def fmt_number(value: float | int | None, decimals: int = 1) -> str:
    """Formatteer een getal met komma als decimaalteken (Nederlandse notatie).

    Parameters
    ----------
    value:    Te formatteren waarde.
    decimals: Aantal decimalen.

    Returns
    -------
    str  Geformatteerd getal (bijv. "3,5") of "-" bij ongeldige invoer.
    """
    try:
        n = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return '-'
    if not math.isfinite(n):
        return '-'
    rounded = round(n, decimals)
    return str(rounded).replace('.', ',')


def format_surcharge_value(points: list[dict]) -> str:
    """Formatteer de waardereeks van een surcharge belasting als kPa-string.

    Parameters
    ----------
    points: Lijst van {'distance', 'value'} dicts.

    Returns
    -------
    str  Bijv. "10,0 kPa" of "5,0–15,0 kPa".
    """
    if not points:
        return ''
    vals = [float(p.get('value', 0)) for p in points]
    min_v = min(vals)
    max_v = max(vals)
    if abs(max_v - min_v) < 1e-9:
        return f'{fmt_number(max_v)} kPa'
    return f'{fmt_number(min_v)}\u2013{fmt_number(max_v)} kPa'


def format_normal_force_values(force) -> str:
    """Formatteer de vier waarden van een normaalkracht als kN/m-string.

    Parameters
    ----------
    force: NormalForce dataclass object.

    Returns
    -------
    str  Bijv. "100,0 kN/m" of "T/SL/SR/B: 100,0/90,0/80,0/70,0 kN/m".
    """
    vals = [
        float(getattr(force, 'top', 0) or 0),
        float(getattr(force, 'surface_left', 0) or 0),
        float(getattr(force, 'surface_right', 0) or 0),
        float(getattr(force, 'bottom', 0) or 0),
    ]
    all_equal = all(abs(v - vals[0]) < 1e-9 for v in vals)
    if all_equal:
        return f'{fmt_number(vals[0])} kN/m'
    joined = '/'.join(fmt_number(v) for v in vals)
    return f'T/SL/SR/B: {joined} kN/m'
