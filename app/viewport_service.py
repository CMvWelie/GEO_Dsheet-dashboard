"""Viewport-berekeningen voor D-Sheet Dashboard."""

from __future__ import annotations

from app.settings import ViewportSettings
from parsers.models import Project, Stage
from renderers.section_renderer import (
    y_range_for_project,
    x_range_for_project,
    get_stage_profile,
)


class ViewportService:
    """Berekent en transformeert viewportinstellingen zonder Qt-kennis."""

    def auto_bounds(self, project: Project) -> ViewportSettings:
        """Bereken automatische x/y-grenzen op basis van projectdata."""
        y_min, y_max = y_range_for_project(project)
        x_min, x_max = x_range_for_project(project)
        return ViewportSettings(auto=True, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)

    def zoom(self, vp: ViewportSettings, factor: float) -> ViewportSettings:
        """Geef een nieuwe ViewportSettings terug geschaald met factor rondom het midden."""
        cx = (vp.x_min + vp.x_max) / 2
        cy = (vp.y_min + vp.y_max) / 2
        hw = (vp.x_max - vp.x_min) / 2 * factor
        hh = (vp.y_max - vp.y_min) / 2 * factor
        return ViewportSettings(
            auto=False,
            x_min=cx - hw, x_max=cx + hw,
            y_min=cy - hh, y_max=cy + hh,
        )

    def get_stage_profile(self, project: Project, stage: Stage | None, side: str):
        """Geef het grondprofiel voor de gegeven fase en zijde."""
        return get_stage_profile(project, stage, side)
