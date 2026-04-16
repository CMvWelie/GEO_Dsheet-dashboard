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


# ==========================================================================
# Oorsprong: ui/tabs/tab_validation.py + app/main_window.py + app/report_controller.py
#            + reporting/validation.py
# Reden: Validatie-tabblad verwijderd op gebruikersverzoek (2026-04-15).
#        TabValidation, ReportValidator, ValidationIssue en alle aanroepen
#        zijn uit de actieve codebase gehaald.
# ==========================================================================

# ---------- reporting/validation.py (volledig) ----------------------------

# from __future__ import annotations
# from dataclasses import dataclass
# from pathlib import Path
# from typing import Literal
# from reporting.models import ReportPackage
#
# @dataclass
# class ValidationIssue:
#     field: str
#     severity: Literal['error', 'warning']
#     message: str
#
# class ReportValidator:
#     """Controleert een ReportPackage op volledigheid en consistentie."""
#     REQUIRED_METADATA = [
#         ('project_name', 'Projectnaam'),
#         ('title',        'Rapporttitel'),
#         ('author',       'Auteur'),
#         ('date',         'Datum'),
#     ]
#
#     def validate(self, package: ReportPackage) -> list[ValidationIssue]:
#         issues: list[ValidationIssue] = []
#         self._check_metadata(package, issues)
#         self._check_items(package, issues)
#         self._check_templates(package, issues)
#         return issues
#
#     def _check_metadata(self, package, issues) -> None:
#         for attr, label in self.REQUIRED_METADATA:
#             if not getattr(package.metadata, attr, ''):
#                 issues.append(ValidationIssue(
#                     field=f'metadata.{attr}', severity='error',
#                     message=f'{label} is verplicht maar niet ingevuld.'))
#
#     def _check_items(self, package, issues) -> None:
#         excel_items = [i for i in package.selected_items if i.included_excel]
#         word_items  = [i for i in package.selected_items if i.included_word]
#         if not package.selected_items:
#             issues.append(ValidationIssue(field='selected_items', severity='warning',
#                 message='Geen rapportage-items geselecteerd.'))
#         elif not excel_items and not word_items:
#             issues.append(ValidationIssue(field='selected_items', severity='warning',
#                 message='Alle items zijn uitgesloten van Excel- én Word-export.'))
#
#     def _check_templates(self, package, issues) -> None:
#         for attr, label in [('template_excel', 'Excel-template'),
#                              ('template_word',  'Word-template')]:
#             path = getattr(package, attr, None)
#             if path and not Path(path).exists():
#                 issues.append(ValidationIssue(field=attr, severity='error',
#                     message=f'{label} bestand niet gevonden: {path}'))

# ---------- ui/tabs/tab_validation.py (volledig) -------------------------

# class TabValidation(QWidget):
#     validate_requested = pyqtSignal()
#
#     def _build(self) -> None:
#         ...  # QTableWidget met kolommen Ernst / Veld / Melding
#
#     def populate(self, issues: list[ValidationIssue]) -> None:
#         ...  # vult tabel en toont samenvatting in _summary_label

# ---------- app/main_window.py — verwijderde regels ----------------------

# from ui.tabs.tab_validation import TabValidation          # import
# self._tab_validation = TabValidation()                    # in _build_tabs
# self._main_tabs.addTab(self._tab_validation, 'Validatie') # in _build_tabs
# self._tab_validation.validate_requested.connect(self._on_validate)  # in _connect_signals
#
# def _on_validate(self) -> None:
#     issues = self._report_controller.validate()
#     self._tab_validation.populate(issues)

# ---------- reporting/selection.py — ReportPlan.remove_item() -----------
# Reden: Verwijder-knop op Selectie-tab verwijderd (2026-04-15).
#        Items worden voortaan alleen via vinkje aan/uitgezet, niet permanent verwijderd.

# def remove_item(self, item_id: str) -> None:
#     """Verwijder item op id."""
#     self.items = [i for i in self.items if i.id != item_id]
#     self._renumber()

# ---------- app/report_controller.py — verwijderde regels ----------------

# from reporting.validation import ReportValidator, ValidationIssue   # import
# self._validator = ReportValidator()                                  # in __init__
#
# def validate(self) -> list[ValidationIssue]:
#     """Valideer het huidige rapportpakket."""
#     return self._validator.validate(self.build_package())
