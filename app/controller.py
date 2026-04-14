"""AppController — applicatielaag van D-Sheet Dashboard.

Orkestreert ingest, parsing, rendering en state-mutaties.
Heeft geen Qt-kennis: retourneert data en status-tuples
zodat de view zelf kan beslissen hoe deze te tonen.
"""

from __future__ import annotations
import io
import logging
import re
from pathlib import Path

_log = logging.getLogger(__name__)

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg

from app.state import AppState
from app.settings import RenderSettings, ViewportSettings, AppSettings
from app.config_manager import ConfigManager
from app.viewport_service import ViewportService
from parsers.models import FileBundle, Project, Stage
from parsers.shi_parser import parse_project
from renderers.section_renderer import SectionRenderer
from renderers.output_renderer import OutputRenderer
from utils.export_manager import ExportManager


class AppController:
    """Applicatielaag: verwerkt gebruikersacties en beheert state-mutaties.

    Weet niets van Qt-widgets; retourneert resultaten als primitieven
    of domeinobjecten zodat de view zelf de presentatie bepaalt.
    """

    def __init__(self, state: AppState) -> None:
        self._state = state
        self._config = ConfigManager()
        self._viewport = ViewportService()
        self._renderer = SectionRenderer()
        self._output_renderer = OutputRenderer()
        self._export = ExportManager()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def load_config(self) -> None:
        """Lees config.json en pas toe op state."""
        rs, vp, app = self._config.load()
        self._state.render_settings = rs
        self._state.viewport_settings = vp
        self._state.app_settings = app

    def save_config(self) -> None:
        """Sla huidige instellingen op."""
        self._config.save(
            self._state.render_settings,
            self._state.viewport_settings,
            self._state.app_settings,
        )

    # ------------------------------------------------------------------
    # Bestandsingest
    # ------------------------------------------------------------------

    def ingest_paths(self, paths: list[str]) -> tuple[bool, str]:
        """Lees bestandsteksten in state.raw_files.

        Returns:
            (True, '') bij succes, (False, foutmelding) bij leesfouten.
        """
        errors: list[str] = []
        loaded = 0
        for path in paths:
            ext = Path(path).suffix.lstrip('.').lower()
            if ext not in ('shi', 'shd', 'shs'):
                continue
            try:
                text = Path(path).read_text(encoding='utf-8', errors='replace')
                self._state.raw_files[Path(path).name] = text
                loaded += 1
            except Exception as exc:
                errors.append(f'{path}: {exc}')
        if errors:
            return False, '\n'.join(errors)
        return True, ''

    def process_files(self) -> tuple[bool, str]:
        """Groepeer raw_files → FileBundle → parse_project → state.projects.

        Returns:
            (True, statusmelding) bij succes, (False, foutmelding) bij fouten.
        """
        grouped: dict[str, dict] = {}
        for name, text in self._state.raw_files.items():
            base = self.group_base_name(name)
            if base not in grouped:
                grouped[base] = {'shi': '', 'shd': '', 'shs': ''}
            ext = Path(name).suffix.lstrip('.').lower()
            if ext in ('shi', 'shd', 'shs'):
                grouped[base][ext] = text

        self._state.projects.clear()
        for base_name, bundle_dict in grouped.items():
            bundle = FileBundle(**bundle_dict)
            self._state.projects[base_name] = parse_project(bundle, base_name)

        if not self._state.projects:
            return False, 'Bestanden konden niet worden gegroepeerd.'

        self._state.active_project = next(iter(self._state.projects))
        self._state.active_stage_index = 0
        self._state.active_output_stage_index = 0

        n = len(self._state.projects)
        return True, f'{n} project(en) ingelezen.'

    def reset(self) -> None:
        """Wis alle state."""
        self._state.reset()

    def remove_project(self, base_name: str) -> None:
        """Verwijder één project en alle bijbehorende raw_files uit de state."""
        for ext in ('shi', 'shd', 'shs'):
            self._state.raw_files.pop(f'{base_name}.{ext}', None)
        self._state.projects.pop(base_name, None)
        if self._state.active_project == base_name:
            self._state.active_project = next(iter(self._state.projects), None)
            self._state.active_stage_index = 0
            self._state.active_output_stage_index = 0

    # ------------------------------------------------------------------
    # Selectie
    # ------------------------------------------------------------------

    def set_active_project(self, key: str) -> None:
        """Stel actief project in en reset fase-indices."""
        if key in self._state.projects:
            self._state.active_project = key
            self._state.active_stage_index = 0
            self._state.active_output_stage_index = 0

    def set_active_stage(self, index: int) -> None:
        """Stel actieve fase-index in."""
        project = self._state.get_active_project()
        n = len(project.stages) if project and project.stages else 1
        self._state.active_stage_index = max(0, min(index, n - 1))

    def set_active_output_stage(self, index: int) -> None:
        """Stel actieve resultaat-fase-index in."""
        project = self._state.get_active_project()
        n = len(project.stages) if project and project.stages else 1
        self._state.active_output_stage_index = max(0, min(index, n - 1))

    def set_active_result_step(self, key: str | None) -> None:
        """Stel actieve VERIFY STEP-sleutel in."""
        self._state.active_result_step = key

    # ------------------------------------------------------------------
    # Viewport
    # ------------------------------------------------------------------

    def apply_auto_viewport(self) -> ViewportSettings | None:
        """Bereken auto-grenzen als auto aan staat; geef nieuwe settings terug of None."""
        project = self._state.get_active_project()
        if project and self._state.viewport_settings.auto:
            vp = self._viewport.auto_bounds(project)
            self._state.viewport_settings = vp
            return vp
        return None

    def apply_zoom(self, factor: float) -> ViewportSettings:
        """Zoom viewport met gegeven factor; zet auto=False."""
        vp = self._viewport.zoom(self._state.viewport_settings, factor)
        self._state.viewport_settings = vp
        return vp

    def reset_viewport(self) -> ViewportSettings:
        """Zet auto=True en herbereken grenzen; geef nieuwe settings terug."""
        self._state.viewport_settings.auto = True
        project = self._state.get_active_project()
        if project:
            vp = self._viewport.auto_bounds(project)
            self._state.viewport_settings = vp
            return vp
        return self._state.viewport_settings

    def compute_auto_viewport(self, project: Project) -> ViewportSettings:
        """Bereken auto-grenzen voor het gegeven project zonder state te muteren."""
        return self._viewport.auto_bounds(project)

    def apply_viewport_settings(self, vp: ViewportSettings) -> None:
        """Sla handmatige viewportinstellingen op in state."""
        self._state.viewport_settings = vp

    def apply_render_settings(self, rs: RenderSettings) -> None:
        """Sla renderinstellingen op in state."""
        self._state.render_settings = rs

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Sla nieuwe app-instellingen op in state en config.

        Parameters
        ----------
        settings:
            Nieuw AppSettings-object met de gewenste waarden.
        """
        self._state.app_settings = settings
        # App-instellingen worden direct opgeslagen (anders dan render/viewport-instellingen
        # die pas bij bewust opslaan worden gepersisteerd).
        self._config.save(
            self._state.render_settings,
            self._state.viewport_settings,
            settings,
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_section(self, ax: Axes, fig: Figure) -> str | None:
        """Render de damwand-doorsnede op de gegeven Axes.

        Returns:
            None bij succes, foutmelding (str) bij een uitzondering.
        """
        project = self._state.get_active_project()
        stage = self._state.get_active_stage()
        if not project:
            return None
        try:
            self._renderer.render(
                ax, project, stage,
                self._state.render_settings,
                self._state.viewport_settings,
            )
            fig.tight_layout()
            return None
        except Exception as exc:
            return str(exc)

    def render_stage_png(self, project: Project, stage: Stage | None,
                          width_px: int = 400, height_px: int = 300,
                          dpi: int = 96) -> bytes | None:
        """Render één fase naar PNG-bytes (Agg, geen Qt vereist)."""
        try:
            vp = self._viewport.auto_bounds(project)
            fig = Figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
            FigureCanvasAgg(fig)
            ax = fig.add_subplot(111)
            self._renderer.render(ax, project, stage,
                                  self._state.render_settings, vp)
            fig.tight_layout(pad=0.3)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
            buf.seek(0)
            return buf.read()
        except Exception:
            _log.exception("render_stage_png mislukt voor project '%s'", project.name)
            return None

    def render_results(self, fig: Figure) -> str | None:
        """Render resultaatgrafieken op de gegeven Figure.

        Returns:
            None bij succes, foutmelding (str) bij een uitzondering.
        """
        project = self._state.get_active_project()
        if not project or not project.result_steps:
            return None
        try:
            self._output_renderer.render_figure(
                fig, project,
                self._state.active_output_stage_index,
                self._state.active_result_step,
                self._state.render_settings,
            )
            return None
        except Exception as exc:
            return str(exc)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_png(self, fig: Figure, path: str) -> str | None:
        """Exporteer figure als PNG.

        Returns:
            None bij succes, foutmelding (str) bij een uitzondering.
        """
        try:
            self._export.export_png(fig, path)
            return None
        except Exception as exc:
            return str(exc)

    # ------------------------------------------------------------------
    # Query-helpers (geen state-mutaties)
    # ------------------------------------------------------------------

    def get_stage_profile(self, side: str):
        """Geef het grondprofiel voor het actieve project/fase en de gegeven zijde."""
        project = self._state.get_active_project()
        stage = self._state.get_active_stage()
        return self._viewport.get_stage_profile(project, stage, side)

    def group_base_name(self, filename: str) -> str:
        """Strip .shi/.shd/.shs-extensie van bestandsnaam."""
        return re.sub(r'\.(shi|shd|shs)$', '', filename, flags=re.IGNORECASE)

    def sort_result_steps(self, keys: list[str]) -> list[str]:
        """Sorteer VERIFY STEP-sleutels op numeriek prefix."""
        return sorted(keys, key=self._result_step_sort)

    @staticmethod
    def _result_step_sort(step: str) -> float:
        m = re.match(r'^(\d+\.\d+)', step)
        val = float(m.group(1)) if m else 999.0
        if 'x 1.2' in step or 'x factor' in step:
            val += 0.01
        return val
