"""InputDescriptionBuilder — bouwt rapportagesecties vanuit projectinvoer."""

from __future__ import annotations
import re
from dataclasses import dataclass, field

from parsers.models import Project, Stage
from reporting.builders.damwand_tekst import (
    DAMWAND_INTRO_TEKST,
    DAMWAND_TOELICHTING_REGELS,
)
from reporting.models import ReportSection, ReportField, ReportTable, TextBlock
from utils.formatting import fmt_number


def _find(lst, name: str):
    return next((x for x in (lst or []) if x.name == name), None)


# ---------------------------------------------------------------------------
# Eenvoudige datastructuur voor fase-kaarten in de tab
# ---------------------------------------------------------------------------

@dataclass
class FaseRow:
    label: str
    value: str
    extra: str = ''
    extra_lines: list[str] = field(default_factory=list)

@dataclass
class FaseCard:
    fase_num: int
    stage_name: str
    rows: list[FaseRow] = field(default_factory=list)
    image_bytes: bytes | None = None


@dataclass
class DamwandCard:
    """Profielgegevens van de damwand (niet fase-specifiek)."""
    profiel: str
    staalkwaliteit: str
    hoogte_mm: float
    breedte_mm: float
    ei_knm2: float
    weerstandsmoment_cm3: float
    opneembaar_moment_knm: float
    kopniveau: float
    teenniveau: float
    lengte: float
    ondersteuningen: list[tuple[str, float]]  # (naam, niveau [m NAP])
    intro_tekst: str = DAMWAND_INTRO_TEKST
    toelichting_regels: list[tuple[str, str]] = field(
        default_factory=lambda: list(DAMWAND_TOELICHTING_REGELS)
    )


class InputDescriptionBuilder:
    """Bouwt een lijst van ReportSection objecten vanuit project/fase invoerdata."""

    # ------------------------------------------------------------------
    # Fase-kaarten (alle fases tegelijk, voor de Invoerbeschrijving-tab)
    # ------------------------------------------------------------------

    def build_all_stages(self, project: Project) -> list[FaseCard]:
        """Bouw een FaseCard per stage met niveau, toelichting en extra regels."""
        cards: list[FaseCard] = []
        for i, stage in enumerate(project.stages, start=1):
            card = FaseCard(fase_num=i, stage_name=stage.name)

            # ── Maaiveld ─────────────────────────────────────────────
            surf_l = _find(project.surfaces, stage.left_surface)
            surf_r = _find(project.surfaces, stage.right_surface)
            y_l = fmt_number(surf_l.points[0]['y']) if surf_l and surf_l.points else '-'
            y_r = fmt_number(surf_r.points[0]['y']) if surf_r and surf_r.points else '-'
            card.rows.append(FaseRow('Maaiveld Links',  f'{y_l} [m NAP]'))
            card.rows.append(FaseRow('Maaiveld Rechts', f'{y_r} [m NAP]'))

            # ── Waterpeilen ──────────────────────────────────────────
            wl_l = _find(project.waterlevels, stage.left_water)
            wl_r = _find(project.waterlevels, stage.right_water)
            w_lv = fmt_number(wl_l.level) if wl_l else '-'
            w_rv = fmt_number(wl_r.level) if wl_r else '-'
            card.rows.append(FaseRow('Water Links',  f'{w_lv} [m NAP]'))
            card.rows.append(FaseRow('Water Rechts', f'{w_rv} [m NAP]'))

            # ── Ankers ───────────────────────────────────────────────
            for name in stage.anchors:
                a = _find(project.anchors, name)
                if a:
                    card.rows.append(FaseRow(
                        a.name,
                        f'{fmt_number(a.level)} [m NAP]',
                        f'{fmt_number(a.angle)} graden t.o.v. maaiveld',
                    ))

            # ── Stempels ─────────────────────────────────────────────
            for name in (stage.struts or []):
                st = _find(project.struts, name)
                if st:
                    card.rows.append(FaseRow(
                        st.name,
                        f'{fmt_number(st.level)} [m NAP]',
                        f'{fmt_number(st.angle)} graden t.o.v. maaiveld',
                        extra_lines=[f'{fmt_number(st.length)} m lengte'],
                    ))

            # ── Veersteunen ──────────────────────────────────────────
            for name in stage.spring_supports:
                s = _find(project.spring_supports, name)
                if s:
                    card.rows.append(FaseRow(
                        s.name,
                        f'{fmt_number(s.level)} [m NAP]',
                        f'{fmt_number(s.rot_stiff)} [kNm/rad]',
                        extra_lines=[f'{fmt_number(s.tr_stiff)} [kN/m]'],
                    ))

            # ── Rigide steunen ───────────────────────────────────────
            for name in stage.rigid_supports:
                r = _find(project.rigid_supports, name)
                if r:
                    card.rows.append(FaseRow(r.name, f'{fmt_number(r.level)} [m NAP]'))

            # ── Normaalkrachten ──────────────────────────────────────
            for name in (stage.normal_forces or []):
                nf = _find(project.normal_forces, name)
                if nf:
                    waarden = [nf.top, nf.surface_left, nf.surface_right, nf.bottom]
                    if len(set(waarden)) == 1:
                        card.rows.append(FaseRow(
                            nf.name, '-', f'{fmt_number(nf.top)} [kN/m]',
                        ))
                    else:
                        card.rows.append(FaseRow(
                            nf.name, '-',
                            f'Top: {fmt_number(nf.top)} [kN/m]',
                            extra_lines=[
                                f'Vlak links: {fmt_number(nf.surface_left)} [kN/m]',
                                f'Vlak rechts: {fmt_number(nf.surface_right)} [kN/m]',
                                f'Bottom: {fmt_number(nf.bottom)} [kN/m]',
                            ],
                        ))

            # ── Gelijkmatige belastingen ─────────────────────────────
            for name in (stage.uniform_loads or []):
                ul = _find(project.uniform_loads, name)
                if ul:
                    val = fmt_number(ul.left) if ul.left else fmt_number(ul.right)
                    card.rows.append(FaseRow(
                        ul.name, 'op maaiveld', f'{val} [kN/m²]',
                    ))

            # ── Surcharge belastingen ────────────────────────────────
            seen: set[str] = set()
            for name in (stage.surcharge_loads_left or []) + (stage.surcharge_loads_right or []):
                if name in seen:
                    continue
                seen.add(name)
                sl = _find(project.surcharge_loads, name)
                if sl and sl.points:
                    val = fmt_number(sl.points[0]['value'])
                    dists = sorted(p['distance'] for p in sl.points)
                    breedte = dists[-1] - dists[0] if len(dists) >= 2 else 0.0
                    afstand = dists[0]
                    card.rows.append(FaseRow(
                        sl.name, 'op maaiveld', f'{val} [kN/m²]',
                        extra_lines=[
                            f'{fmt_number(breedte)}m breed',
                            f'{fmt_number(afstand)}m vanaf damwand',
                        ],
                    ))

            # ── Momenten ─────────────────────────────────────────────
            for name in (stage.moments or []):
                m = _find(project.moments, name)
                if m:
                    card.rows.append(FaseRow(
                        m.name,
                        f'{fmt_number(m.level)} [m NAP]',
                        f'{fmt_number(m.value)} [kNm/m]',
                    ))

            # ── Horizontale lijnlasten ───────────────────────────────
            for name in (stage.horizontal_line_loads or []):
                hl = _find(project.horizontal_line_loads, name)
                if hl:
                    card.rows.append(FaseRow(
                        hl.name,
                        f'{fmt_number(hl.level)} [m NAP]',
                        f'{fmt_number(hl.value)} [kN/m]',
                    ))

            cards.append(card)
        return cards

    def build_damwand_card(self, project: Project) -> DamwandCard | None:
        """Bouw een DamwandCard vanuit het eerste SheetPilingElement.

        Parameters
        ----------
        project:
            Actief project.

        Returns
        -------
        DamwandCard | None
            None als geen sheet piling aanwezig.
        """
        if not project.sheet_piling:
            return None
        el = project.sheet_piling[0]

        # Profielnaam: verwijder staalkwaliteit-deel "(S240GP)"
        profiel_naam = re.sub(r'\s*\([^)]+\)\s*$', '', el.name).strip()

        # Ondersteuningsniveaus: alle typen die in minstens één fase actief zijn
        actieve_ankers: set[str] = set()
        actieve_stempels: set[str] = set()
        actieve_rigid: set[str] = set()
        actieve_spring: set[str] = set()
        for stage in project.stages:
            actieve_ankers.update(stage.anchors or [])
            actieve_stempels.update(stage.struts or [])
            actieve_rigid.update(stage.rigid_supports or [])
            actieve_spring.update(stage.spring_supports or [])

        steunen: list[tuple[str, float]] = []
        for anker in project.anchors:
            if anker.name in actieve_ankers:
                steunen.append((anker.name, anker.level))
        for stempel in project.struts:
            if stempel.name in actieve_stempels:
                steunen.append((stempel.name, stempel.level))
        for steun in project.rigid_supports:
            if steun.name in actieve_rigid:
                steunen.append((steun.name, steun.level))
        for steun in project.spring_supports:
            if steun.name in actieve_spring:
                steunen.append((steun.name, steun.level))
        steunen.sort(key=lambda t: t[1], reverse=True)

        return DamwandCard(
            profiel=profiel_naam,
            staalkwaliteit=el.steel_quality,
            hoogte_mm=el.height_mm,
            breedte_mm=el.pile_width_mm,
            ei_knm2=el.ei_knm2_per_m,
            weerstandsmoment_cm3=el.resisting_moment_cm3,
            opneembaar_moment_knm=el.opneembaar_moment_knm,
            kopniveau=el.top if el.top is not None else 0.0,
            teenniveau=el.bottom,
            lengte=abs((el.top or 0.0) - el.bottom),
            ondersteuningen=steunen,
        )

    def build(self, project: Project, stage: Stage,
              overrides: dict[str, str] | None = None) -> list[ReportSection]:
        self._overrides = overrides or {}
        sections = []
        sections.append(self._sheet_piling(project))
        sections.append(self._geometry(project, stage))
        sections.append(self._water(project, stage))
        sections.append(self._loads(project, stage))
        sections.append(self._anchors(project, stage))
        sections.append(self._struts(project, stage))
        sections.append(self._supports(project, stage))
        sections.append(self._soil_layers(project, stage))
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
    # Secties
    # ------------------------------------------------------------------

    def _sheet_piling(self, project: Project) -> ReportSection:
        sec = ReportSection(id='sheet_piling', title='Damwand')
        for wall in project.sheet_piling:
            sec.fields.append(ReportField('wall_name', 'Naam', wall.name))
            sec.fields.append(ReportField('wall_x', 'x-positie', fmt_number(wall.x), 'm'))
            sec.fields.append(ReportField('wall_top', 'Bovenzijde',
                                           fmt_number(wall.top) if wall.top is not None else '-', 'm NAP'))
            sec.fields.append(ReportField('wall_bottom', 'Onderzijde',
                                           fmt_number(wall.bottom), 'm NAP'))
        if project.sheet_piling:
            w = project.sheet_piling[0]
            top_s = fmt_number(w.top) if w.top is not None else '?'
            gen = (f'De damwand heeft een bovenzijde op {top_s} m NAP en een '
                   f'onderzijde op {fmt_number(w.bottom)} m NAP '
                   f'(totale lengte {fmt_number(abs(w.bottom - (w.top or 0.0)))} m).')
        else:
            gen = 'Er zijn geen damwandpalen gedefinieerd.'
        sec.text_blocks.append(self._tb('sheet_piling', gen))
        return sec

    def _geometry(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='geometry', title='Geometrie actieve fase')
        sec.fields.append(ReportField('left_surface', 'Maaiveld links',
                                       stage.left_surface or '-'))
        sec.fields.append(ReportField('right_surface', 'Maaiveld rechts',
                                       stage.right_surface or '-'))
        sec.fields.append(ReportField('left_profile', 'Grondprofiel links',
                                       stage.left_profile or '-'))
        sec.fields.append(ReportField('right_profile', 'Grondprofiel rechts',
                                       stage.right_profile or '-'))
        return sec

    def _water(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='water', title='Waterpeilen actieve fase')
        sec.fields.append(ReportField('left_water', 'Waterpeil links',
                                       stage.left_water or '-'))
        sec.fields.append(ReportField('right_water', 'Waterpeil rechts',
                                       stage.right_water or '-'))
        rows = [[w.name, fmt_number(w.level)] for w in project.waterlevels]
        if rows:
            sec.tables.append(ReportTable(
                id='waterlevels', title='Waterpeilen',
                columns=['Naam', 'Peil [m NAP]'], rows=rows))
        return sec

    def _loads(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='loads', title='Belastingen actieve fase')
        # Uniform loads
        active_ul = [_find(project.uniform_loads, n) for n in stage.uniform_loads]
        active_ul = [u for u in active_ul if u]
        if active_ul:
            rows = [[u.name, fmt_number(u.left), fmt_number(u.right),
                     fmt_number(u.permanent), fmt_number(u.favourable)]
                    for u in active_ul]
            sec.tables.append(ReportTable(
                id='uniform_loads', title='Gelijkmatige belastingen',
                columns=['Naam', 'Links [kN/m²]', 'Rechts [kN/m²]',
                         'Permanent', 'Gunstig'],
                rows=rows))
        # Surcharge loads
        all_surcharge_names = list(dict.fromkeys(
            stage.surcharge_loads_left + stage.surcharge_loads_right))
        active_sq = [_find(project.surcharge_loads, n) for n in all_surcharge_names]
        active_sq = [s for s in active_sq if s]
        if active_sq:
            rows = [[s.name, str(len(s.points))] for s in active_sq]
            sec.tables.append(ReportTable(
                id='surcharge_loads', title='Surcharge belastingen',
                columns=['Naam', 'Aantal punten'], rows=rows))
        return sec

    def _anchors(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='anchors', title='Ankers actieve fase')
        active = [_find(project.anchors, n) for n in stage.anchors]
        active = [a for a in active if a]
        if active:
            rows = [[a.name, fmt_number(a.level), fmt_number(a.length),
                     fmt_number(a.angle), fmt_number(a.yield_f)]
                    for a in active]
            sec.tables.append(ReportTable(
                id='anchors', title='Ankers',
                columns=['Naam', 'Niveau [m NAP]', 'Lengte [m]',
                         'Hoek [°]', 'Vloeigrens [kN]'],
                rows=rows))
            names = ', '.join(a.name for a in active)
            gen = (f'In deze fase zijn {len(active)} anker(s) actief: {names}. '
                   f'De ankers bevinden zich op niveaus variërend van '
                   f'{fmt_number(min(a.level for a in active))} tot '
                   f'{fmt_number(max(a.level for a in active))} m NAP.')
        else:
            sec.fields.append(ReportField('anchors_none', 'Ankers', 'Geen actief'))
            gen = 'In deze fase zijn geen ankers actief.'
        sec.text_blocks.append(self._tb('anchors', gen))
        return sec

    def _struts(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='struts', title='Stempels actieve fase')
        active = [_find(project.struts, n) for n in stage.struts]
        active = [s for s in active if s]
        if active:
            rows = [[s.name, fmt_number(s.level), fmt_number(s.length),
                     fmt_number(s.angle), fmt_number(s.yield_f)]
                    for s in active]
            sec.tables.append(ReportTable(
                id='struts', title='Stempels',
                columns=['Naam', 'Niveau [m NAP]', 'Lengte [m]',
                         'Hoek [°]', 'Vloeigrens [kN]'],
                rows=rows))
            names = ', '.join(s.name for s in active)
            gen = f'In deze fase zijn {len(active)} stempel(s) actief: {names}.'
        else:
            sec.fields.append(ReportField('struts_none', 'Stempels', 'Geen actief'))
            gen = 'In deze fase zijn geen stempels actief.'
        sec.text_blocks.append(self._tb('struts', gen))
        return sec

    def _supports(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='supports', title='Steunen actieve fase')
        active_sp = [_find(project.spring_supports, n) for n in stage.spring_supports]
        active_sp = [s for s in active_sp if s]
        if active_sp:
            rows = [[s.name, fmt_number(s.level), fmt_number(s.rot_stiff),
                     fmt_number(s.tr_stiff)] for s in active_sp]
            sec.tables.append(ReportTable(
                id='spring_supports', title='Veersteunen',
                columns=['Naam', 'Niveau [m NAP]', 'Rotatiestijfheid', 'Translatiestijfheid'],
                rows=rows))
        active_rg = [_find(project.rigid_supports, n) for n in stage.rigid_supports]
        active_rg = [r for r in active_rg if r]
        if active_rg:
            rows = [[r.name, fmt_number(r.level)] for r in active_rg]
            sec.tables.append(ReportTable(
                id='rigid_supports', title='Rigide steunen',
                columns=['Naam', 'Niveau [m NAP]'],
                rows=rows))
        if not active_sp and not active_rg:
            sec.fields.append(ReportField('supports_none', 'Steunen', 'Geen actief'))
        return sec

    def _soil_layers(self, project: Project, stage: Stage) -> ReportSection:
        sec = ReportSection(id='soil_layers', title='Grondlagen actieve fase')
        for side, profile_name in [('Links', stage.left_profile),
                                    ('Rechts', stage.right_profile)]:
            profile = next((p for p in project.profiles
                            if p.name == profile_name), None)
            if not profile:
                continue
            rows = []
            for i, layer in enumerate(profile.layers):
                bottom = (fmt_number(profile.layers[i + 1].level)
                          if i + 1 < len(profile.layers) else '...')
                rows.append([str(layer.nr), layer.material,
                             fmt_number(layer.level), bottom])
            sec.tables.append(ReportTable(
                id=f'soil_layers_{side.lower()}',
                title=f'Grondlagen {side} — {profile.name}',
                columns=['Nr', 'Materiaal', 'Bovenzijde [m NAP]', 'Onderzijde [m NAP]'],
                rows=rows))
        return sec
