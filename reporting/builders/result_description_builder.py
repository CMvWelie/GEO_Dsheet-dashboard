"""ResultDescriptionBuilder — bouwt rapportagesecties vanuit rekenresultaten."""

from __future__ import annotations

from parsers.models import Project
from reporting.models import ReportSection, ReportField, ReportTable
from utils.formatting import fmt_number


# CUR 166 verification_type → label, in vaste rekenvolgorde
_VTYPE_VOLGORDE: list[int] = [4, 5, 0, 1, 3, 14]
_VTYPE_LABELS: dict[int, str] = {
    4: '6.1', 5: '6.2', 0: '6.3', 1: '6.4', 3: '6.5', 14: '6.5 × factor',
}


def _vtype_label(vtype: int) -> str:
    return _VTYPE_LABELS.get(vtype, f'V{vtype}')


class ResultDescriptionBuilder:
    """Bouwt een lijst van ReportSection objecten vanuit D-Sheet rekenresultaten."""

    def build(self, project: Project, stage_index: int,
              step_key: str | None,
              overrides: dict[str, str] | None = None) -> list[ReportSection]:
        stage = (project.stages[stage_index]
                 if 0 <= stage_index < len(project.stages) else None)
        fase_naam = stage.name if stage else str(stage_index + 1)
        sections = []
        sections.append(self._anchor_forces(project))
        sections.append(self._per_phase_summary(project, step_key))
        return sections

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _stage_naam(self, project: Project, stage_number: int) -> str:
        if 0 <= stage_number - 1 < len(project.stages):
            return project.stages[stage_number - 1].name
        return f'Fase {stage_number}'

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

    def _anchor_forces(self, project: Project) -> ReportSection:
        sec = ReportSection(id='anchor_forces',
                            title='Ankerkrachten en stempelkrachten')
        alle_items = project.anchor_strut_resume
        if not alle_items:
            sec.fields.append(ReportField('anchor_forces_none', 'Ankerkrachten',
                                           'Geen resultaten beschikbaar'))
            return sec

        # Kolommen: CUR 166 vtype in vaste volgorde, alleen aanwezige
        aanwezige_vtypes = {r.verification_type for r in alle_items}
        stappen = [v for v in _VTYPE_VOLGORDE if v in aanwezige_vtypes]
        columns = ['Fase'] + [_vtype_label(v) for v in stappen]

        # Rijen: alle fases van het project (1-gebaseerd), niet alleen aanwezige
        alle_stages = list(range(1, len(project.stages) + 1))

        # Eén tabel per ankernaam
        voor_naam: dict[str, list] = {}
        for r in alle_items:
            voor_naam.setdefault(r.name, []).append(r)

        for naam in sorted(voor_naam):
            items = voor_naam[naam]
            lookup: dict[tuple[int, int], float] = {
                (r.stage_number, r.verification_type): r.force for r in items
            }

            rows: list[list[str]] = []
            for sn in alle_stages:
                rij = [self._stage_naam(project, sn)]
                for vtype in stappen:
                    waarde = lookup.get((sn, vtype))
                    rij.append(fmt_number(waarde) if waarde is not None else '-')
                rows.append(rij)
            sec.tables.append(ReportTable(
                id=f'anker_{naam}',
                title=naam,
                columns=columns,
                rows=rows,
            ))
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
            stage_name = self._stage_naam(project, stage_num)
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
                columns=['Fase', 'Max. moment [kNm/m]', 'Max. dwarskracht [kN/m]',
                         'Max. vervorming [mm]'],
                rows=rows))
        return sec
