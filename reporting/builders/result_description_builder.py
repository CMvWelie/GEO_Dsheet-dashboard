"""ResultDescriptionBuilder — bouwt rapportagesecties vanuit rekenresultaten."""

from __future__ import annotations

from parsers.models import Project
from reporting.models import ReportSection, ReportField, ReportTable, TextBlock
from utils.formatting import fmt_number


class ResultDescriptionBuilder:
    """Bouwt een lijst van ReportSection objecten vanuit D-Sheet rekenresultaten."""

    def build(self, project: Project, stage_index: int,
              step_key: str | None,
              overrides: dict[str, str] | None = None) -> list[ReportSection]:
        self._overrides = overrides or {}
        result_stage = self._get_result_stage(project, step_key, stage_index + 1)
        sections = []
        sections.append(self._moment_max(result_stage))
        sections.append(self._shear_max(result_stage))
        sections.append(self._displacement_max(result_stage))
        sections.append(self._anchor_forces(project, stage_index + 1))
        sections.append(self._per_phase_summary(project, step_key))
        return sections

    def _tb(self, sec_id: str, generated: str) -> TextBlock:
        block_id = f'{sec_id}_desc'
        return TextBlock(
            id=block_id,
            section=sec_id,
            generated_text=generated,
            manual_override=self._overrides.get(block_id) or None,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_result_stage(self, project: Project, step_key: str | None,
                           stage_number: int):
        if not step_key or step_key not in project.result_steps:
            return None
        return project.result_steps[step_key].stages.get(stage_number)

    def _extremes(self, result_stage, attr: str):
        """Geeft (max_val, max_depth, min_val, min_depth) of None bij geen data."""
        if not result_stage or not result_stage.points:
            return None
        vals = [(getattr(p, attr, 0.0) or 0.0, p.depth) for p in result_stage.points]
        max_v, max_d = max(vals, key=lambda t: t[0])
        min_v, min_d = min(vals, key=lambda t: t[0])
        return max_v, max_d, min_v, min_d

    # ------------------------------------------------------------------
    # Secties
    # ------------------------------------------------------------------

    def _moment_max(self, result_stage) -> ReportSection:
        sec = ReportSection(id='moment_max', title='Maximale momenten')
        ex = self._extremes(result_stage, 'moment')
        if ex:
            max_v, max_d, min_v, min_d = ex
            sec.fields += [
                ReportField('moment_max', 'Maximum moment', fmt_number(max_v), 'kNm'),
                ReportField('moment_max_depth', 'Diepte maximum', fmt_number(max_d), 'm NAP'),
                ReportField('moment_min', 'Minimum moment', fmt_number(min_v), 'kNm'),
                ReportField('moment_min_depth', 'Diepte minimum', fmt_number(min_d), 'm NAP'),
            ]
            gen = (f'Het maximale buigend moment bedraagt {fmt_number(max_v)} kNm op '
                   f'{fmt_number(max_d)} m NAP. Het minimale moment bedraagt '
                   f'{fmt_number(min_v)} kNm op {fmt_number(min_d)} m NAP.')
        else:
            sec.fields.append(ReportField('moment_none', 'Momenten', 'Geen resultaten beschikbaar'))
            gen = 'Geen momentresultaten beschikbaar voor deze fase/stap.'
        sec.text_blocks.append(self._tb('moment_max', gen))
        return sec

    def _shear_max(self, result_stage) -> ReportSection:
        sec = ReportSection(id='shear_max', title='Maximale dwarskrachten')
        ex = self._extremes(result_stage, 'shear')
        if ex:
            max_v, max_d, min_v, min_d = ex
            sec.fields += [
                ReportField('shear_max', 'Maximum dwarskracht', fmt_number(max_v), 'kN'),
                ReportField('shear_max_depth', 'Diepte maximum', fmt_number(max_d), 'm NAP'),
                ReportField('shear_min', 'Minimum dwarskracht', fmt_number(min_v), 'kN'),
                ReportField('shear_min_depth', 'Diepte minimum', fmt_number(min_d), 'm NAP'),
            ]
            gen = (f'De maximale dwarskracht bedraagt {fmt_number(max_v)} kN op '
                   f'{fmt_number(max_d)} m NAP.')
        else:
            sec.fields.append(ReportField('shear_none', 'Dwarskrachten', 'Geen resultaten beschikbaar'))
            gen = 'Geen dwarskrachtresultaten beschikbaar voor deze fase/stap.'
        sec.text_blocks.append(self._tb('shear_max', gen))
        return sec

    def _displacement_max(self, result_stage) -> ReportSection:
        sec = ReportSection(id='displacement_max', title='Maximale vervormingen')
        ex = self._extremes(result_stage, 'disp')
        if ex:
            max_v, max_d, min_v, min_d = ex
            sec.fields += [
                ReportField('disp_max', 'Maximum vervorming', fmt_number(max_v), 'mm'),
                ReportField('disp_max_depth', 'Diepte maximum', fmt_number(max_d), 'm NAP'),
                ReportField('disp_min', 'Minimum vervorming', fmt_number(min_v), 'mm'),
                ReportField('disp_min_depth', 'Diepte minimum', fmt_number(min_d), 'm NAP'),
            ]
            max_abs = max(abs(max_v), abs(min_v))
            gen = (f'De maximale vervorming van de damwand bedraagt '
                   f'{fmt_number(max_abs)} mm.')
        else:
            sec.fields.append(ReportField('disp_none', 'Vervormingen', 'Geen resultaten beschikbaar'))
            gen = 'Geen vervormingsresultaten beschikbaar voor deze fase/stap.'
        sec.text_blocks.append(self._tb('displacement_max', gen))
        return sec

    def _anchor_forces(self, project: Project, stage_number: int) -> ReportSection:
        sec = ReportSection(id='anchor_forces', title='Ankerkrachten en stempelkrachten')
        items = [r for r in project.anchor_strut_resume
                 if r.stage_number == stage_number]
        if items:
            rows = [[r.name, fmt_number(r.force), str(r.anchor_state)]
                    for r in items]
            sec.tables.append(ReportTable(
                id='anchor_strut_forces', title='Anker-/stempelkrachten',
                columns=['Naam', 'Kracht [kN]', 'Status'],
                rows=rows))
        else:
            sec.fields.append(ReportField('anchor_forces_none', 'Ankerkrachten',
                                           'Geen resultaten beschikbaar'))
        return sec

    def _per_phase_summary(self, project: Project, step_key: str | None) -> ReportSection:
        sec = ReportSection(id='per_phase_summary', title='Samenvatting per fase')
        if not step_key or step_key not in project.result_steps:
            sec.fields.append(ReportField('summary_none', 'Samenvatting',
                                           'Geen resultaatstap geselecteerd'))
            return sec

        step = project.result_steps[step_key]
        rows = []
        for stage_num in sorted(step.stages.keys()):
            rs = step.stages[stage_num]
            stage = (project.stages[stage_num - 1]
                     if 0 <= stage_num - 1 < len(project.stages) else None)
            stage_name = stage.name if stage else str(stage_num)
            ex_m = self._extremes(rs, 'moment')
            ex_s = self._extremes(rs, 'shear')
            ex_d = self._extremes(rs, 'disp')
            max_m = fmt_number(max(abs(ex_m[0]), abs(ex_m[2]))) if ex_m else '-'
            max_s = fmt_number(max(abs(ex_s[0]), abs(ex_s[2]))) if ex_s else '-'
            max_d = fmt_number(max(abs(ex_d[0]), abs(ex_d[2]))) if ex_d else '-'
            rows.append([stage_name, max_m, max_s, max_d])
        if rows:
            sec.tables.append(ReportTable(
                id='phase_summary', title='Per fase samenvatting',
                columns=['Fase', 'Max. moment [kNm]', 'Max. dwarskracht [kN]',
                         'Max. vervorming [mm]'],
                rows=rows))
        return sec
