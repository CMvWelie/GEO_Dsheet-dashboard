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
            for j, rij in enumerate(kaart.rows):
                sec.fields.append(ReportField(
                    key=f'fase_{i + 1}_{j}_{rij.label.lower().replace(" ", "_")}',
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

    # ------------------------------------------------------------------
    # Sectie 4: Conclusietabel per fase
    # ------------------------------------------------------------------

    def _bouw_conclusietabel(self, project: Project) -> ReportSection:
        """Bouw conclusietabel met resultaten per fase.

        Parameters
        ----------
        project:
            Actief project met resultaatsamenvatting per fase.

        Returns
        -------
        ReportSection
            Sectie met één tabel; geen tabel als er geen summaries zijn.
        """
        sec = ReportSection(id='conclusietabel', title='Resultaten per fase')
        if not project.result_summaries:
            return sec
        kolommen = [
            'Fase', 'Max |M| [kNm/m]', 'Max |V| [kN/m]',
            'Max |u| [mm]', 'Mob. moment [%]', 'Mob. grond [%]',
        ]
        rijen: list[list[str]] = []
        for rs in sorted(project.result_summaries, key=lambda r: r.stage_number):
            fase_naam = (project.stages[rs.stage_number - 1].name
                         if 0 <= rs.stage_number - 1 < len(project.stages)
                         else str(rs.stage_number))
            rijen.append([
                fase_naam,
                fmt_number(rs.max_moment_knm),
                fmt_number(rs.max_shear_kn),
                fmt_number(rs.max_disp_mm),
                fmt_number(rs.mob_moment_pct),
                fmt_number(rs.mob_grond_pct),
            ])
        sec.tables.append(ReportTable(
            id='conclusietabel_tabel',
            title='',
            columns=kolommen,
            rows=rijen,
        ))
        return sec

    # ------------------------------------------------------------------
    # Sectie 5: Resultatengrafieken
    # ------------------------------------------------------------------

    def _governing_stage_index(self, project: Project) -> int:
        """Geef de 0-gebaseerde index van de fase met het hoogste absoluut moment.

        Parameters
        ----------
        project:
            Actief project.

        Returns
        -------
        int
            Index van de maatgevende fase; 0 als er geen summaries zijn.
        """
        if not project.result_summaries:
            return max(0, len(project.stages) - 1)
        best = max(project.result_summaries, key=lambda r: r.max_moment_knm)
        return best.stage_number - 1

    def _bouw_grafiek_secties(
        self,
        project: Project,
        governing_step_key: str | None,
        disp_step_key: str | None,
    ) -> list[ReportSection]:
        """Bouw twee grafiek-secties: moment/dwarskracht (ULS) en vervorming (6.5).

        Parameters
        ----------
        project:
            Actief project.
        governing_step_key:
            Sleutel van de maatgevende resultaatstap (ULS).
        disp_step_key:
            Sleutel van de vervormingsstap (bevat '6.5').

        Returns
        -------
        list[ReportSection]
            Twee secties: moment/dwarskracht en vervorming.
        """
        gov_idx = self._governing_stage_index(project)
        sec_mv = ReportSection(id='grafieken_moment_dwarskracht',
                               title='Momenten en dwarskrachten')
        sec_mv.images.append(ReportImageRequest(
            id='grafiek_moment_shear',
            caption='Momenten en dwarskrachten — maatgevende fase',
            figure_key='moment_shear',
            stage_index=gov_idx,
            step_key=governing_step_key,
        ))
        sec_disp = ReportSection(id='grafieken_vervorming', title='Vervormingen')
        sec_disp.images.append(ReportImageRequest(
            id='grafiek_displacement',
            caption='Vervormingen — stap 6.5',
            figure_key='displacement',
            stage_index=gov_idx,
            step_key=disp_step_key,
        ))
        return [sec_mv, sec_disp]

    # ------------------------------------------------------------------
    # Hoofd-methode
    # ------------------------------------------------------------------

    def build(
        self,
        project: Project,
        governing_step_key: str | None,
        disp_step_key: str | None,
    ) -> list[ReportSection]:
        """Bouw alle vijf secties van het damwand-hoofdstuk.

        Parameters
        ----------
        project:
            Actief project.
        governing_step_key:
            Sleutel van de maatgevende resultaatstap (ULS) voor moment/dwarskracht.
        disp_step_key:
            Sleutel van de resultaatstap voor vervorming (bevat '6.5').

        Returns
        -------
        list[ReportSection]
            Secties in volgorde: grondlagen, damwand, fases, conclusie, grafieken.
        """
        secties: list[ReportSection] = []
        secties += SoilTableBuilder().build(project)             # 1. Grondlagen
        secties.append(self._bouw_damwand_sectie(project))       # 2. Damwandgegevens
        secties += self._bouw_fase_secties(project)              # 3. Invoer per fase
        secties.append(self._bouw_conclusietabel(project))       # 4. Conclusietabel
        secties += self._bouw_grafiek_secties(                   # 5. Grafieken
            project, governing_step_key, disp_step_key
        )
        return secties
