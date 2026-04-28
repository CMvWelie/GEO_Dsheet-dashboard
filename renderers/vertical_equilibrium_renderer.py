"""Renderer voor de visualisatie van verticaal evenwicht."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from matplotlib.axes import Axes

from app.settings import RenderSettings, ViewportSettings
from parsers.models import Project, Stage, Surface
from renderers import BaseRenderer
from renderers.section_renderer import SectionRenderer
from utils.formatting import fmt_number
from utils.geometry import surface_y_at


@dataclass
class VerticalEquilibriumContext:
    """Invoerwaarden voor de verticaal-evenwicht-overlay."""

    profiel_zijde: str
    ontgravingsniveau: float
    waterpeil_bouwput: float
    stijghoogte: float
    watergewicht: float
    evenwichtsniveau: float | None
    grondlagen: list[tuple[str, float, float, float, float]] = field(default_factory=list)


class VerticalEquilibriumRenderer(BaseRenderer):
    """Render doorsnede plus markeringen voor verticaal evenwicht."""

    def __init__(self) -> None:
        self._section_renderer = SectionRenderer()
        self.context = VerticalEquilibriumContext(
            profiel_zijde='links',
            ontgravingsniveau=0.0,
            waterpeil_bouwput=0.0,
            stijghoogte=0.0,
            watergewicht=10.0,
            evenwichtsniveau=None,
        )

    def set_context(self, context: VerticalEquilibriumContext) -> None:
        """Stel de actuele overlay-invoer in.

        Parameters
        ----------
        context:
            Actuele waarden uit het tabblad Verticaal evenwicht.
        """
        self.context = context

    def render(
        self,
        ax: Axes,
        project: Project,
        stage: Stage | None,
        settings: RenderSettings,
        viewport: ViewportSettings,
    ) -> None:
        """Render de doorsnede zonder standaardbelastingen/waterpeilen plus VE-overlay."""
        render_project = replace(project, waterlevels=[])
        render_stage = self._stage_zonder_belastingen(stage)
        self._section_renderer.render(ax, render_project, render_stage, settings, viewport)
        self._teken_overlay(ax, project, stage)

    def _stage_zonder_belastingen(self, stage: Stage | None) -> Stage | None:
        """Maak een renderkopie waarin externe belastingen niet worden getekend."""
        if stage is None:
            return None
        return replace(
            stage,
            uniform_loads=[],
            surcharge_loads=[],
            surcharge_loads_left=[],
            surcharge_loads_right=[],
            horizontal_line_loads=[],
            moments=[],
            normal_forces=[],
        )

    def _teken_overlay(self, ax: Axes, project: Project, stage: Stage | None) -> None:
        """Teken markeringen specifiek voor de verticaal-evenwichtcontrole."""
        context = self.context
        if context.evenwichtsniveau is None:
            return

        surface = self._toets_surface(project, stage)
        vdst = max(0.0, (context.stijghoogte - context.evenwichtsniveau) * context.watergewicht)
        x_links, x_rechts, surface_bodem = self._toetslijn_geometrie(project, surface, ax)
        if x_links is None or x_rechts is None:
            return

        y_toets = context.ontgravingsniveau
        if surface_bodem is not None and abs(y_toets - surface_bodem) > 0.05:
            y_toets = surface_bodem

        ax.plot(
            [x_links, x_rechts], [y_toets, y_toets],
            color='#d84315', linewidth=4.2, solid_capstyle='round',
            clip_on=True, zorder=20,
        )
        ax.text(
            (x_links + x_rechts) / 2.0, y_toets + 0.12,
            'toetslijn verticaal evenwicht',
            ha='center', va='bottom', fontsize=8.5,
            color='#bf360c', fontweight='bold',
            clip_on=True, zorder=21,
        )

        self._teken_niveaulijnen(ax, project, x_links, x_rechts, y_toets)
        self._teken_waterdrukpijlen(ax, x_links, x_rechts, y_toets, vdst)

    def _teken_niveaulijnen(
        self,
        ax: Axes,
        project: Project,
        x_links: float,
        x_rechts: float,
        y_toets: float,
    ) -> None:
        """Teken evenwichtsniveau, stijghoogte, peilbuis en bouwputwaterpeil."""
        context = self.context
        if context.evenwichtsniveau is None:
            return

        ax.plot(
            [x_links, x_rechts], [context.evenwichtsniveau, context.evenwichtsniveau],
            color='#1565c0', linewidth=2.0, linestyle='--',
            clip_on=True, zorder=18,
        )
        ax.text(
            x_rechts, context.evenwichtsniveau - 0.10,
            f'evenwichtsniveau ({fmt_number(context.evenwichtsniveau, 2)})',
            ha='right', va='top', fontsize=8.0,
            color='#1565c0', clip_on=True, zorder=21,
        )
        ax.plot(
            [x_links, x_rechts], [context.stijghoogte, context.stijghoogte],
            color='#0d47a1', linewidth=1.6, linestyle=':',
            clip_on=True, zorder=18,
        )
        self._teken_peilbuis(ax, project, x_links, x_rechts, y_toets)

        ax.plot(
            [x_links, x_rechts], [context.waterpeil_bouwput, context.waterpeil_bouwput],
            color='#42a5f5', linewidth=1.5, linestyle='-.',
            clip_on=True, zorder=18,
        )
        ax.text(
            x_rechts, context.waterpeil_bouwput + 0.08,
            f'waterpeil bouwput ({fmt_number(context.waterpeil_bouwput, 2)})',
            ha='right', va='bottom', fontsize=8.0,
            color='#1976d2', clip_on=True, zorder=21,
        )

    def _teken_waterdrukpijlen(
        self,
        ax: Axes,
        x_links: float,
        x_rechts: float,
        y_toets: float,
        vdst: float,
    ) -> None:
        """Teken opwaartse waterdrukpijlen onder het evenwichtsniveau."""
        context = self.context
        if vdst <= 0.0 or context.evenwichtsniveau is None:
            return

        breedte = max(0.0, x_rechts - x_links)
        if breedte <= 0.05:
            return
        n_pijlen = max(3, min(9, int(round(breedte / 1.2))))
        marge = min(0.35, breedte / (n_pijlen + 1) * 0.35)
        pijl_lengte = max(0.6, min(1.8, abs(y_toets - context.evenwichtsniveau) * 0.35))
        pijl_start_y = context.evenwichtsniveau - pijl_lengte
        pijl_eind_y = context.evenwichtsniveau - 0.08
        if pijl_eind_y <= pijl_start_y:
            return
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(min(y_min, pijl_start_y - 0.3), y_max)

        for i in range(n_pijlen):
            x = x_links + marge + (breedte - 2 * marge) * (i + 0.5) / n_pijlen
            ax.annotate(
                '', xy=(x, pijl_eind_y), xytext=(x, pijl_start_y),
                arrowprops=dict(arrowstyle='-|>', color='#1565c0', lw=1.7),
                annotation_clip=True, clip_on=True, zorder=22,
            )

        ax.text(
            (x_links + x_rechts) / 2.0,
            (pijl_start_y + pijl_eind_y) / 2.0,
            f'Vdst;d = {fmt_number(vdst, 2)} kN/m²',
            ha='center', va='center', fontsize=8.5,
            color='#0d47a1',
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='#90caf9', alpha=0.86),
            clip_on=True, zorder=23,
        )

    def _teken_peilbuis(
        self,
        ax: Axes,
        project: Project,
        x_links: float,
        x_rechts: float,
        y_toets: float,
    ) -> None:
        """Teken een peilbuis met waterniveau gelijk aan de stijghoogte."""
        context = self.context
        breedte = max(0.1, x_rechts - x_links)
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        damwand_x = self._damwand_x(project)
        plaats_links = context.profiel_zijde != 'links'
        if plaats_links:
            buis_x = damwand_x - max(0.45, (damwand_x - x_min) / 6.0)
            label_x = buis_x - max(0.35, breedte * 0.04)
            label_ha = 'right'
        else:
            buis_x = damwand_x + max(0.45, (x_max - damwand_x) / 6.0)
            label_x = buis_x + max(0.35, breedte * 0.04)
            label_ha = 'left'

        buis_half_breedte = max(0.06, min(0.12, breedte * 0.018))
        buis_top = max(y_toets + 0.6, context.stijghoogte + 0.6)
        buis_bot = self._midden_onderste_zichtbare_laag(y_min, y_max)
        ax.set_ylim(min(y_min, buis_bot - 0.2), max(y_max, buis_top + 0.2))

        ax.plot(
            [buis_x - buis_half_breedte, buis_x - buis_half_breedte],
            [buis_bot, buis_top],
            color='#263238', linewidth=1.4, clip_on=True, zorder=24,
        )
        ax.plot(
            [buis_x + buis_half_breedte, buis_x + buis_half_breedte],
            [buis_bot, buis_top],
            color='#263238', linewidth=1.4, clip_on=True, zorder=24,
        )
        ax.plot(
            [buis_x - buis_half_breedte, buis_x + buis_half_breedte],
            [buis_bot, buis_bot],
            color='#263238', linewidth=1.4, clip_on=True, zorder=24,
        )

        water_top = min(context.stijghoogte, buis_top)
        water_bot = min(buis_bot, water_top)
        ax.fill_between(
            [buis_x - buis_half_breedte * 0.78, buis_x + buis_half_breedte * 0.78],
            [water_bot, water_bot],
            [water_top, water_top],
            color='#64b5f6', alpha=0.72, clip_on=True, zorder=23,
        )
        ax.plot(
            [buis_x - buis_half_breedte * 1.4, buis_x + buis_half_breedte * 1.4],
            [context.stijghoogte, context.stijghoogte],
            color='#0d47a1', linewidth=2.0, clip_on=True, zorder=25,
        )
        ax.text(
            label_x, context.stijghoogte,
            f'peilbuis stijghoogte {fmt_number(context.stijghoogte, 2)}',
            ha=label_ha, va='center', fontsize=8.0,
            color='#0d47a1', clip_on=True, zorder=25,
        )

    def _toets_surface(self, project: Project, stage: Stage | None) -> Surface | None:
        """Zoek de surface die bij de gekozen profielzijde hoort."""
        if not stage:
            return None
        surface_naam = stage.left_surface if self.context.profiel_zijde == 'links' else stage.right_surface
        return next((surface for surface in project.surfaces if surface.name == surface_naam), None)

    def _toetslijn_geometrie(
        self,
        project: Project,
        surface: Surface | None,
        ax: Axes,
    ) -> tuple[float | None, float | None, float | None]:
        """Bepaal x-bereik en niveau van de getoetste surfaceline."""
        if surface and surface.points:
            x_links, x_rechts, surface_bodem = _zoek_bodem_punten(surface)
            if abs(x_rechts - x_links) > 0.05:
                return x_links, x_rechts, surface_bodem

        wall_x = self._damwand_x(project)
        x_min, x_max = ax.get_xlim()
        if self.context.profiel_zijde == 'links':
            x_links, x_rechts = x_min, wall_x
        else:
            x_links, x_rechts = wall_x, x_max
        if abs(x_rechts - x_links) <= 0.05:
            return None, None, None

        surface_niveau = self._surface_niveau_op_bereik(surface, x_links, x_rechts)
        return x_links, x_rechts, surface_niveau

    def _damwand_x(self, project: Project) -> float:
        """Lees de x-positie van de damwand met 0 als terugval."""
        if project.sheet_piling:
            x = project.sheet_piling[0].x
            if math.isfinite(x):
                return x
        return 0.0

    def _surface_niveau_op_bereik(
        self,
        surface: Surface | None,
        x_links: float,
        x_rechts: float,
    ) -> float | None:
        """Lees het surfaceniveau in het midden van een zichtbaar toetsbereik."""
        if not surface or not surface.points:
            return None
        return surface_y_at(surface.points, (x_links + x_rechts) / 2.0)

    def _midden_onderste_zichtbare_laag(self, y_min: float, y_max: float) -> float:
        """Bepaal het midden van de onderste laag die in de visualisatie zichtbaar is."""
        onderste_mid: float | None = None
        for _naam, bk, ok, _gamma_dr, _gamma_nat in self.context.grondlagen:
            zichtbaar_boven = min(bk, y_max)
            zichtbaar_onder = max(ok, y_min)
            if zichtbaar_boven <= zichtbaar_onder:
                continue
            mid = (zichtbaar_boven + zichtbaar_onder) / 2.0
            if onderste_mid is None or mid < onderste_mid:
                onderste_mid = mid
        if onderste_mid is not None:
            return onderste_mid
        return y_min + (y_max - y_min) * 0.15


def _zoek_bodem_punten(surface: Surface) -> tuple[float, float, float]:
    """Geeft (x_links, x_rechts, min_y) van de laagste Surface-punten."""
    min_y = min(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_links = min(pt['x'] for pt in bodem)
    x_rechts = max(pt['x'] for pt in bodem)
    return x_links, x_rechts, min_y
