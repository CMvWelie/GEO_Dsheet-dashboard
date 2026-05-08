"""ResultDescriptionBuilder — bouwt rapportagesecties vanuit rekenresultaten."""

from __future__ import annotations

import re
from collections.abc import Callable

from parsers.models import Project
from reporting.models import (
    ReportImageGroup,
    ReportImageRequest,
    ReportSection,
    ReportField,
    ReportTable,
)
from utils.formatting import fmt_number


_ANCHOR_TYPE_LABELS: dict[int, str] = {0: 'Anker', 1: 'Stempel'}
_SUPPORT_RIGIDITY_LABELS: dict[int, str] = {0: 'Veersteun', 1: 'Stijve steun'}

# CUR 166 verification_type → label, in vaste rekenvolgorde
_VTYPE_VOLGORDE: list[int] = [4, 5, 0, 1, 3, 14]
_VTYPE_LABELS: dict[int, str] = {
    4: '6.1', 5: '6.2', 0: '6.3', 1: '6.4', 3: '6.5', 14: '6.5 × factor',
}


_UGT_LABELS: set[str] = {'6.1', '6.2', '6.3', '6.4', '6.5 x factor'}
_BGT_LABELS: set[str] = {'6.5'}


def _vtype_label(vtype: int) -> str:
    return _VTYPE_LABELS.get(vtype, f'V{vtype}')


def _step_short_label(key: str) -> str:
    """Extraheer korte CUR 166-staplabel uit de genormaliseerde sleutel.

    Parameters
    ----------
    key: Genormaliseerde sleutelstring, bijv. '6.1' of '6.5 x factor'.

    Returns
    -------
    str  Kort label, bijv. '6.1' of '6.5 × factor'.
    """
    m = re.search(r'(\d+\.\d+(?:\s+[x×]\s+factor)?)', key, re.IGNORECASE)
    if m:
        return re.sub(r'\s+[x×]\s+factor', ' × factor', m.group(1),
                      flags=re.IGNORECASE)
    return key


def _step_norm_label(key: str) -> str:
    """Geef een vergelijkbaar CUR 166-staplabel terug.

    Parameters
    ----------
    key:
        Genormaliseerde of ruwe VERIFY STEP-sleutel.

    Returns
    -------
    str
        Label in kleine letters, met ``x factor`` zonder typografisch teken.
    """
    label = _step_short_label(key).replace('×', 'x')
    return re.sub(r'\s+', ' ', label).strip().lower()


def is_ugt_step_key(key: str) -> bool:
    """Geef True als een stap volgens de app-definitie UGT is.

    UGT omvat CUR 166 stappen 6.1 t/m 6.4 en 6.5 x factor. De gewone
    stap 6.5 is BGT en telt niet mee voor Msd/Dsd.
    """
    return _step_norm_label(key) in _UGT_LABELS


def is_bgt_step_key(key: str) -> bool:
    """Geef True als een stap volgens de app-definitie BGT is."""
    return _step_norm_label(key) in _BGT_LABELS


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
        sections.append(self._build_extremen_overzicht(project))
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

    def _find_extreme(
        self,
        project: Project,
        attr: str,
        step_filter=None,
    ) -> tuple[float, int, str, float] | None:
        """Vind het absolute extremum over alle fases en toegestane stappen.

        Parameters
        ----------
        project:
            Project met ``result_steps``.
        attr:
            Attribuut op ``ResultPoint``: ``moment``, ``shear`` of ``disp``.
        step_filter:
            Optionele callable die een stap-sleutel accepteert en ``True``
            teruggeeft als de stap moet meetellen.

        Returns
        -------
        tuple[float, int, str, float] | None
            ``(waarde, fase_nummer, stap_key, diepte)`` van het absolute
            maximum, of ``None`` als er geen data is.
        """
        beste: tuple[float, int, str, float] | None = None
        for stap_key, step in project.result_steps.items():
            if step_filter is not None and not step_filter(stap_key):
                continue
            for stage_num, result_stage in step.stages.items():
                ex = self._extremes(result_stage, attr)
                if ex is None:
                    continue
                max_v, max_d, min_v, min_d = ex
                for waarde, diepte in [(max_v, max_d), (min_v, min_d)]:
                    if beste is None or abs(waarde) > abs(beste[0]):
                        beste = (waarde, stage_num, stap_key, diepte)
        return beste

    # ------------------------------------------------------------------
    # Secties
    # ------------------------------------------------------------------

    def _anchor_forces(self, project: Project) -> ReportSection:
        sec = ReportSection(id='anchor_forces',
                            title='Ankerkrachten, stempelkrachten en ondersteuningen')
        alle_stages = list(range(1, len(project.stages) + 1))

        heeft_ankers = bool(project.anchor_strut_resume)
        heeft_steunen = bool(project.supports_resume)

        if not heeft_ankers and not heeft_steunen:
            sec.fields.append(ReportField('anchor_forces_none', 'Ankerkrachten',
                                           'Geen resultaten beschikbaar'))
            return sec

        if heeft_ankers:
            self._voeg_kracht_tabellen_toe(
                sec, project.anchor_strut_resume, 'anker', alle_stages, project,
                lambda r: _ANCHOR_TYPE_LABELS.get(r.anchor_type, f'type {r.anchor_type}'))
        if heeft_steunen:
            self._voeg_steun_tabellen_toe(sec, project.supports_resume, alle_stages, project)
        return sec

    def _voeg_kracht_tabellen_toe(
        self,
        sec: ReportSection,
        items: list,
        id_prefix: str,
        alle_stages: list[int],
        project: Project,
        type_label_fn: Callable[[object], str] | None = None,
    ) -> None:
        """Voeg per naam één krachttabel toe aan sec."""
        aanwezige_vtypes = {r.verification_type for r in items}
        stappen = [v for v in _VTYPE_VOLGORDE if v in aanwezige_vtypes]
        columns = ['Fase'] + [_vtype_label(v) for v in stappen]

        voor_naam: dict[str, list] = {}
        for r in items:
            voor_naam.setdefault(r.name, []).append(r)

        for naam in sorted(voor_naam):
            groep = voor_naam[naam]
            type_label = type_label_fn(groep[0]) if type_label_fn else ''
            tabel_titel = naam
            lookup: dict[tuple[int, int], float] = {
                (r.stage_number, r.verification_type): r.force for r in groep
            }
            rows: list[list[str]] = []
            for sn in alle_stages:
                rij = [self._stage_naam(project, sn)]
                for vtype in stappen:
                    waarde = lookup.get((sn, vtype))
                    rij.append(fmt_number(waarde) if waarde is not None else '-')
                rows.append(rij)
            sec.tables.append(ReportTable(
                id=f'{id_prefix}_{naam}',
                title=tabel_titel,
                columns=columns,
                rows=rows,
            ))

    def _voeg_steun_tabellen_toe(
        self,
        sec: ReportSection,
        items: list,
        alle_stages: list[int],
        project: Project,
    ) -> None:
        """Voeg per naam kracht- en/of momenttabel toe voor veersteunen/stijve steunen."""
        aanwezige_vtypes = {r.verification_type for r in items}
        stappen = [v for v in _VTYPE_VOLGORDE if v in aanwezige_vtypes]
        columns = ['Fase'] + [_vtype_label(v) for v in stappen]

        steun_heeft_kracht: set[str] = set()
        steun_heeft_moment: set[str] = set()
        for r in items:
            if abs(r.force) > 1e-6:
                steun_heeft_kracht.add(r.name)
            if abs(r.moment) > 1e-6:
                steun_heeft_moment.add(r.name)

        voor_naam: dict[str, list] = {}
        for r in items:
            voor_naam.setdefault(r.name, []).append(r)

        for naam in sorted(voor_naam):
            groep = voor_naam[naam]
            toon_kracht = naam in steun_heeft_kracht
            toon_moment = naam in steun_heeft_moment
            beide = toon_kracht and toon_moment

            if toon_kracht:
                lookup_f = {(r.stage_number, r.verification_type): r.force for r in groep}
                rows_f: list[list[str]] = []
                for sn in alle_stages:
                    rij = [self._stage_naam(project, sn)]
                    for vtype in stappen:
                        waarde = lookup_f.get((sn, vtype))
                        rij.append(fmt_number(waarde) if waarde is not None else '-')
                    rows_f.append(rij)
                sec.tables.append(ReportTable(
                    id=f'ondersteuning_{naam}_kracht',
                    title=f'{naam} — kracht [kN/m]' if beide else naam,
                    columns=columns,
                    rows=rows_f,
                ))

            if toon_moment:
                lookup_m = {(r.stage_number, r.verification_type): r.moment for r in groep}
                rows_m: list[list[str]] = []
                for sn in alle_stages:
                    rij = [self._stage_naam(project, sn)]
                    for vtype in stappen:
                        waarde = lookup_m.get((sn, vtype))
                        rij.append(fmt_number(waarde) if waarde is not None else '-')
                    rows_m.append(rij)
                sec.tables.append(ReportTable(
                    id=f'ondersteuning_{naam}_moment',
                    title=f'{naam} — moment [kNm/m]' if beide else naam,
                    columns=columns,
                    rows=rows_m,
                ))

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

    def _build_extremen_overzicht(self, project: Project) -> ReportSection:
        """Bouw de 3x3 figuurtabel met Msd, Dsd en Urep BGT.

        Msd en Dsd worden bepaald uit UGT-stappen 6.1 t/m 6.4 plus
        6.5 x factor. Urep BGT wordt bepaald uit de gewone stap 6.5.
        """
        sec = ReportSection(
            id='extremen_overzicht',
            title='Maatgevende resultaten',
        )
        if not project.result_steps:
            sec.fields.append(ReportField(
                'extremen_none',
                'Maatgevende resultaten',
                'Geen resultaten beschikbaar',
            ))
            return sec

        msd = self._find_extreme(project, 'moment', is_ugt_step_key)
        dsd = self._find_extreme(project, 'shear', is_ugt_step_key)
        urep = self._find_extreme(project, 'disp', is_bgt_step_key)

        kolommen = [
            ('Msd', 'moment_curve', 'kNm/m', msd),
            ('Dsd', 'shear_curve', 'kN/m', dsd),
            ('Urep BGT', 'disp_curve', 'mm', urep),
        ]

        headers: list[str] = []
        images: list[ReportImageRequest | None] = []
        footers: list[str] = []
        for label, figure_key, eenheid, extreme in kolommen:
            if extreme is None:
                headers.append(f'{label} = -')
                images.append(None)
                footers.append('-')
                continue

            waarde, stage_num, stap_key, _diepte = extreme
            headers.append(f'{label} = {fmt_number(abs(waarde))} {eenheid}')
            footers.append(
                f'Fase {stage_num} - {self._stage_naam(project, stage_num)}; '
                f'stap {_step_short_label(stap_key)}'
            )
            images.append(ReportImageRequest(
                id=f'extreme_{label.lower().replace(" ", "_")}',
                caption='',
                figure_key=figure_key,
                stage_index=stage_num - 1,
                step_key=stap_key,
            ))

        sec.image_groups.append(ReportImageGroup(
            id='extremen_3x3',
            title='',
            headers=headers,
            images=images,
            footers=footers,
        ))
        return sec
