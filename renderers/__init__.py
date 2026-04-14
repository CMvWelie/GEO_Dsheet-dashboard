"""Renderer-pakket met abstracte basisklasse."""

from __future__ import annotations
from abc import ABC, abstractmethod
from matplotlib.axes import Axes

from app.settings import RenderSettings, ViewportSettings
from parsers.models import Project, Stage


class BaseRenderer(ABC):
    """Abstracte basisklasse voor alle D-Sheet renderers."""

    @abstractmethod
    def render(
        self,
        ax: Axes,
        project: Project,
        stage: Stage | None,
        settings: RenderSettings,
        viewport: ViewportSettings,
    ) -> None:
        """Render de visualisatie op de gegeven Axes.

        Parameters
        ----------
        ax:       Matplotlib Axes om op te tekenen.
        project:  Het actieve projectobject.
        stage:    De actieve bouwfase (kan None zijn).
        settings: Renderschaalinstellingen.
        viewport: Viewport-bereik instellingen.
        """
