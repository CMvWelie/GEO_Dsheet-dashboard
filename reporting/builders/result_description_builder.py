"""ResultDescriptionBuilder — bouwt rapportagesecties vanuit rekenresultaten."""

from __future__ import annotations

import re

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


def _step_short_label(key: str) -> str:
    """Extraheer korte CUR 166-staplabel uit de genormaliseerde sleutel.

    Parameters
    ----------
    key: Genormaliseerde sleutelstring, bijv. 'CUR 166 6.1' of 'CUR 166 6.5 x factor'.

    Returns
    -------
    str  Kort label, bijv. '6.1' of '6.5 × factor'.
    """
    m = re.search(r'(\d+\.\d+(?:\s+x\s+factor)?)', key, re.IGNORECASE)
    if m:
        return m.group(1).replace(' x factor', ' × factor')
    return key


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
        sections.append(self._per_phase_summary(project))
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

    def _per_phase_summary(self, project: Project) -> ReportSection:
        sec = ReportSection(id='per_phase_summary',
                            title='Maximale resultaten per fase')
        if not project.result_steps:
            sec.fields.append(ReportField('summary_none', 'Samenvatting',
                                           'Geen resultaten beschikbaar'))
            return sec

        # Stappen gesorteerd; alle fases
        stap_keys = sorted(project.result_steps.keys())
        alle_stages = list(range(1, len(project.stages) + 1))
        stap_labels = [_step_short_label(sk) for sk in stap_keys]
        n = len(stap_labels)

        # Één brede tabel: Fase | stap… (Momenten) | stap… (Dwarskrachten) | stap… (Vervormingen)
        kolommen = (
            ['Fase']
            + list(stap_labels)
            + list(stap_labels)
            + list(stap_labels)
        )
        sep_cols = [1 + n, 1 + 2 * n]  # begin Dwarskrachten- en Vervormingen-groep

        rows: list[list[str]] = []
        for stage_num in alle_stages:
            rij: list[str] = [self._stage_naam(project, stage_num)]
            for attr in ('moment', 'shear', 'disp'):
                for sk in stap_keys:
                    step = project.result_steps[sk]
                    rs = step.stages.get(stage_num)
                    ex = self._extremes(rs, attr) if rs else None
                    rij.append(
                        fmt_number(max(abs(ex[0]), abs(ex[2]))) if ex else '-'
                    )
            rows.append(rij)

        sec.tables.append(ReportTable(
            id='summary_resultaten',
            title='',
            columns=kolommen,
            rows=rows,
            separator_before_cols=sep_cols,
            column_groups=[
                ('', 1),
                ('Momenten (kNm)', n),
                ('Dwarskrachten (kN)', n),
                ('Vervormingen (mm)', n),
            ],
        ))
        return sec
