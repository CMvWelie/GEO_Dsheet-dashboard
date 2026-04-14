"""Dode code archief — D-Sheet Dashboard.

Bevat code die uit de actieve codebase is verwijderd maar bewaard wordt
voor raadpleging. Niets in dit bestand wordt geïmporteerd of uitgevoerd.

Indeling per origineel bestand, met vermelding van reden van verwijdering.
"""

# ==========================================================================
# Oorsprong: renderers/draw_helpers.py
# Reden: imports nooit gebruikt in het bestand (geverifieerd via grep)
# ==========================================================================

# import matplotlib.patches as mpatches          # dubbele + ongebruikte import
# from matplotlib.patches import FancyArrowPatch  # nooit aangeroepen
# from matplotlib.patches import FancyArrow       # nooit aangeroepen
# from matplotlib.lines import Line2D             # nooit aangeroepen
# import matplotlib.path as mpath                 # nooit aangeroepen
# import matplotlib.patches as patches            # dubbele import van mpatches


# ==========================================================================
# Oorsprong: utils/geometry.py
# Reden: functie nergens in de codebase aangeroepen (geverifieerd via grep)
# ==========================================================================

def build_uniform_load_polygon(
    surface_points: list[dict],
    x_start: float,
    x_end: float,
    height_data: float,
) -> list[tuple[float, float]]:
    """Bouw een polygoon voor een uniforme belasting boven het maaiveld.

    Parameters
    ----------
    surface_points: Maaiveldpunten als {'x', 'y'} dicts.
    x_start:        Begin x-coördinaat.
    x_end:          Eind x-coördinaat.
    height_data:    Hoogte van de belastingblok in data-eenheden (meters).

    Returns
    -------
    list[tuple[float, float]]  Polygoon in datacoördinaten.
    """
    from utils.geometry import clip_surface_points
    clipped = clip_surface_points(surface_points, x_start, x_end)
    if len(clipped) < 2:
        return []
    top = [(p['x'], p['y'] + height_data) for p in clipped]
    bottom = [(p['x'], p['y']) for p in reversed(clipped)]
    return top + bottom


# ==========================================================================
# Oorsprong: utils/export_manager.py — ExportManager.export_pdf()
# Reden: methode nergens aangeroepen; stub met "voor later" in docstring
# ==========================================================================

# class ExportManager:  # (fragment)
#     def export_pdf(self, figure, filepath) -> None:
#         """Exporteer een matplotlib-figuur als PDF-bestand."""
#         figure.savefig(str(filepath), format='pdf', bbox_inches='tight')


# ==========================================================================
# Oorsprong: ui/tabs/tab_input_desc.py — TabInputDesc.populate()
# Reden: backwards-compat stub op QWidget zonder basisklasse die het definieert;
#        _tab_input_desc.populate() wordt nergens in main_window.py aangeroepen
# ==========================================================================

# class TabInputDesc:  # (fragment)
#     def populate(self, sections) -> None:  # type: ignore[override]
#         pass
