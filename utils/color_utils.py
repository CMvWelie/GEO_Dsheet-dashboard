"""Kleurconversie hulpfuncties voor D-Sheet grondkleuren."""

from __future__ import annotations


def parse_color_int(n: int | str | None) -> str:
    """Converteer een D-Sheet integer kleurwaarde naar een CSS rgb()-string.

    D-Sheet slaat kleuren op als een 24-bit integer in BGR volgorde
    (Windows COLORREF-formaat): R = bits 0-7, G = bits 8-15, B = bits 16-23.

    Parameters
    ----------
    n: Integer kleurwaarde uit het .shd-bestand.

    Returns
    -------
    str  CSS kleurstring, bijv. "rgb(120, 200, 80)".
    """
    value = int(n) if n is not None else 0
    r = value & 0xFF
    g = (value >> 8) & 0xFF
    b = (value >> 16) & 0xFF
    return f'rgb({r}, {g}, {b})'


def rgb_string_to_tuple(rgb: str) -> tuple[float, float, float]:
    """Converteer een "rgb(r, g, b)" string naar een matplotlib-compatibele tuple (0-1).

    Parameters
    ----------
    rgb: CSS kleurstring zoals "rgb(120, 200, 80)".

    Returns
    -------
    tuple[float, float, float]  (r, g, b) elk in bereik [0, 1].
    """
    import re
    m = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb)
    if m:
        return (int(m.group(1)) / 255, int(m.group(2)) / 255, int(m.group(3)) / 255)
    return (0.86, 0.86, 0.86)


def color_for_matplotlib(color: str) -> tuple[float, float, float]:
    """Geef een matplotlib-kleur tuple terug voor een CSS kleurstring.

    Ondersteunt 'rgb(r,g,b)' strings en standaard CSS-namen.

    Parameters
    ----------
    color: Kleurstring (bijv. "rgb(120,200,80)" of "#aabbcc").

    Returns
    -------
    tuple  RGB-tuple bruikbaar als matplotlib facecolor.
    """
    if color.startswith('rgb('):
        return rgb_string_to_tuple(color)
    return color  # type: ignore[return-value]  # matplotlib accepteert ook hex/namen
