"""DamwandHoofdstukBuilder — bouwt het volledige damwand-rapportagehoofdstuk."""
from __future__ import annotations

import re

from parsers.models import Project, Stage
from reporting.models import ReportSection, ReportField, ReportTable, ReportImageRequest
from reporting.builders.soil_table_builder import SoilTableBuilder
from reporting.builders.input_description_builder import InputDescriptionBuilder
from utils.formatting import fmt_number


def _find(lst: list | None, name: str) -> object | None:
    return next((x for x in (lst or []) if x.name == name), None)


class DamwandHoofdstukBuilder:
    """Bouwt alle vijf secties van het damwand-rapportagehoofdstuk."""

    # ------------------------------------------------------------------
    # Sectie 2: Damwandgegevens
    # ------------------------------------------------------------------

    def _bouw_damwand_sectie(self, project: Project) -> ReportSection:
        """Bouw sectie met profieleigenschappen van de damwand.

        Parameters
        ----------
        project:
            Actief project met damwandgegevens.

        Returns
        -------
        ReportSection
            Sectie met velden voor het damwandprofiel; lege fields als er
            geen damwand aanwezig is.
        """
        sec = ReportSection(id='damwand_gegevens', title='Damwandgegevens')
        if not project.sheet_piling:
            return sec
        w = project.sheet_piling[0]
        profiel_naam = re.sub(r'\s*\([^)]+\)\s*$', '', w.name).strip()
        lengte_str = fmt_number(abs(w.top - w.bottom)) if w.top is not None else '-'
        sec.fields = [
            ReportField('profiel',           'Profiel',                    profiel_naam),
            ReportField('staalkwaliteit',    'Staalkwaliteit',              w.steel_quality),
            ReportField('hoogte_mm',         'Hoogte',                      fmt_number(w.height_mm),             'mm'),
            ReportField('breedte_mm',        'Breedte',                     fmt_number(w.pile_width_mm),         'mm'),
            ReportField('ei_knm2',           'Buigstijfheid EI',            fmt_number(w.ei_knm2_per_m),        'kNm²/m'),
            ReportField('wel_cm3',           'Weerstandsmoment Wy;el',      fmt_number(w.resisting_moment_cm3), 'cm³/m'),
            ReportField('opneembaar_moment', 'Opneembaar moment',           fmt_number(w.opneembaar_moment_knm), 'kNm/m'),
            ReportField('kopniveau',         'Kopniveau',                   fmt_number(w.top) if w.top is not None else '-', 'm NAP'),
            ReportField('teenniveau',        'Teenniveau',                  fmt_number(w.bottom),               'm NAP'),
            ReportField('lengte',            'Lengte',                      lengte_str,                         'm'),
        ]
        return sec

    # ------------------------------------------------------------------
    # Sectie 3: Invoer per fase
    # ------------------------------------------------------------------

    def _bouw_fase_secties(self, project: Project) -> list[ReportSection]:
        """Bouw één ReportSection per constructiefase, inclusief een figuurverzoek.

        Parameters
        ----------
        project:
            Actief project met een of meer fases.

        Returns
        -------
        list[ReportSection]
            Lijst van secties, één per fase; leeg als het project geen fases heeft.
        """
        idb = InputDescriptionBuilder()
        kaarten = idb.build_all_stages(project)
        secties: list[ReportSection] = []
        for i, kaart in enumerate(kaarten):
            sec = ReportSection(
                id=f'fase_{i + 1}_invoer',
                title=f'Fase {kaart.fase_num}: {kaart.stage_name}',
            )
            for rij in kaart.rows:
                sec.fields.append(ReportField(
                    key=f'fase_{i + 1}_{rij.label.lower().replace(" ", "_")}',
                    label=rij.label,
                    value=rij.value,
                    unit=rij.extra,
                ))
            sec.images.append(ReportImageRequest(
                id=f'fase_{i + 1}_doorsnede',
                caption=f'Dwarsdoorsnede fase {kaart.fase_num}',
                figure_key='section',
                stage_index=i,
                step_key=None,
            ))
            secties.append(sec)
        return secties
