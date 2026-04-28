"""Instellingen-dataclasses voor rendering en viewport."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RenderSettings:
    """Schaalinstellingen voor het tekenen van belastingen en momenten."""
    uniform_meters_per_10kpa: float = 0.5
    """Hoogte van uniforme belastingblok: hoeveel meter per 10 kPa."""
    normal_meters_per_10knm: float = 0.5
    """Breedte van normaalkrachtdiagram: hoeveel meter per 10 kN/m."""
    hload_scale: float = 2.0
    """Stemlengthe (m) voor horizontale lijnlasten."""
    moment_radius_meters: float = 1.0
    """Radius van het momentensymbool in meters."""

    # Tekstgroottes (pt)
    fs_grondlagen: float = 9.0
    fs_knikpunten: float = 7.5
    fs_waterpeil: float = 8.0
    fs_belastingen: float = 8.5
    fs_constructie: float = 8.5
    """Ankers, stempels, veren, rigide steunen en aanhechtingslabels."""
    fs_damwand: float = 8.5
    """Segmentnamen, kop- en teen-niveau."""
    fs_assen: float = 10.0
    """As-labels en tick-labels."""
    fs_titel: float = 12.0

    # Doorsnede-symbolen
    waterpeil_schaal: float = 1.0
    """Schalfactor voor het waterpeils-symbool (golflijntjes en verticale stap)."""
    maaiveld_schaal: float = 1.0
    """Schalfactor voor de driehoekbreedte van het maaiveld-symbool."""

    # Resultaatgrafieken
    resultaat_half_breedte_m: float = 10.0
    """Halve zichtbare breedte in meters voor resultaatgrafieken, gecentreerd op de damwand."""


@dataclass
class ViewportSettings:
    """Zichtbereik-instellingen voor het canvas."""
    auto: bool = True
    """Automatisch bereik bepalen op basis van projectdata."""
    x_min: float = -10.0
    x_max: float = 10.0
    y_min: float = -10.0
    y_max: float = 5.0


@dataclass
class AppSettings:
    """Algemene applicatie-instellingen."""
    word_template_path: str = ''
    """Pad naar het Word-sjabloon (.dotx, ook .docx ondersteund); leeg = geen sjabloon."""
    standaard_importmap: str = ''
    """Standaard startmap voor het importeer-dialoogvenster; leeg = systeemstandaard."""
