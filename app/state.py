"""Centrale applicatie-state als dataclass."""

from __future__ import annotations
from dataclasses import dataclass, field

from app.settings import RenderSettings, ViewportSettings, AppSettings
from parsers.models import Project


@dataclass
class AppState:
    """Centrale staat van de D-Sheet Dashboard applicatie.

    Bevat alle projectdata, selecties en instellingen. Er is
    exact één instantie per applicatierun; UI-componenten
    lezen en schrijven hiernaartoe via Qt-signals.
    """
    projects: dict[str, Project] = field(default_factory=dict)
    """Alle ingelezen projecten, geïndexeerd op base_name."""

    active_project: str | None = None
    """base_name van het actief geselecteerde project."""

    active_stage_index: int = 0
    """Index van de actieve bouwfase (voor de doorsnede-weergave)."""

    active_output_stage_index: int = 0
    """Index van de actieve bouwfase (voor de resultaatgrafieken)."""

    active_result_step: str | None = None
    """Genormaliseerde sleutel van de actieve VERIFY STEP."""

    raw_files: dict[str, str] = field(default_factory=dict)
    """Ruwe bestandsteksten: filename → text."""

    render_settings: RenderSettings = field(default_factory=RenderSettings)
    viewport_settings: ViewportSettings = field(default_factory=ViewportSettings)
    app_settings: AppSettings = field(default_factory=AppSettings)
    """Algemene applicatie-instellingen (template-pad, etc.)."""

    def get_active_project(self) -> Project | None:
        """Geef het actieve Project-object terug, of None."""
        if self.active_project is None:
            return None
        return self.projects.get(self.active_project)

    def get_active_stage(self, project: Project | None = None):
        """Geef de actieve Stage terug, of None."""
        proj = project or self.get_active_project()
        if not proj or not proj.stages:
            return None
        idx = min(self.active_stage_index, len(proj.stages) - 1)
        return proj.stages[idx]

    def reset(self) -> None:
        """Wis alle projectdata en reset selecties naar beginwaarden."""
        self.projects.clear()
        self.raw_files.clear()
        self.active_project = None
        self.active_stage_index = 0
        self.active_output_stage_index = 0
        self.active_result_step = None
        self.render_settings = RenderSettings()
        self.viewport_settings = ViewportSettings()
        self.app_settings = AppSettings()
