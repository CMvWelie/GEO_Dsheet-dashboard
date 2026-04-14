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
    hload_low_scale: float = 1.0
    """Steemlengthe (m) voor horizontale lijnlasten < 30 kN/m."""
    hload_mid_scale: float = 2.0
    """Stemlengthe (m) voor horizontale lijnlasten 30-60 kN/m."""
    hload_high_scale: float = 3.0
    """Steemlengthe (m) voor horizontale lijnlasten > 60 kN/m."""
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
