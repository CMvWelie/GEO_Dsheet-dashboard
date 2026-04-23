"""Tab Debug Invoer — toont alle geparste invoerdata als scrollbare sectielijst."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
)
from PyQt6.QtCore import Qt

from parsers.models import (
    Project, Anchor, Strut, SpringSupport, RigidSupport,
    UniformLoad, SurchargeLoad, HorizontalLineLoad, Moment, NormalForce, Stage,
)

# ── Stijlconstanten ──────────────────────────────────────────────────────────
_FONT      = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
_HDR_BG    = '#1b3a5c'
_HDR_FG    = '#ffffff'
_SUBHDR_BG = '#274f77'
_SUBHDR_FG = '#b8d4ea'

# ── Kolomdefinities ──────────────────────────────────────────────────────────
_ANCHOR_HDRS    = ['nr', 'name', 'level', 'E-mod', 'doorsnede', 'lengte',
                   'vloeigrens', 'hoek', 'hoogte', 'zijde']
_STRUT_HDRS     = ['nr', 'name', 'level', 'E-mod', 'doorsnede', 'lengte',
                   'vloeigrens', 'hoek', 'aux', 'zijde']
_SPRING_HDRS    = ['nr', 'name', 'level', 'rot_stiff', 'tr_stiff']
_RIGID_HDRS     = ['nr', 'name', 'level', 'rot_stiff', 'tr_stiff']
_UNIFORM_HDRS   = ['name', 'links', 'rechts', 'permanent', 'gunstig']
_SURCHARGE_HDRS = ['afstand', 'waarde']
_LIJNLAST_HDRS  = ['nr', 'name', 'level', 'waarde', 'permanent', 'gunstig']
_MOMENT_HDRS    = ['nr', 'name', 'level', 'waarde', 'permanent', 'gunstig']
_NORMAAL_HDRS   = ['nr', 'name', 'top', 'vlak_links', 'vlak_rechts',
                   'bottom', 'permanent', 'gunstig']


def _find(lst, naam: str):
    return next((x for x in (lst or []) if x.name == naam), None)


def _maak_header(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(
        f'font-family: {_FONT}; font-size: 11px; font-weight: 700; '
        f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 6px 10px; '
        f'margin-top: 8px;'
    )
    lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return lbl


def _maak_subheader(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(
        f'font-family: {_FONT}; font-size: 11px; font-weight: 600; '
        f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; padding: 4px 10px;'
    )
    lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return lbl


def _maak_tabel(headers: list[str], rijen: list[list[str]]) -> QTableWidget:
    tabel = QTableWidget(len(rijen), len(headers))
    tabel.setHorizontalHeaderLabels(headers)
    tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabel.setAlternatingRowColors(True)
    tabel.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    tabel.verticalHeader().setVisible(False)
    tabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    tabel.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    tabel.setStyleSheet(f'font-family: {_FONT}; font-size: 11px;')
    for r, rij in enumerate(rijen):
        for c, cel in enumerate(rij):
            tabel.setItem(r, c, QTableWidgetItem('' if cel is None else str(cel)))
    tabel.resizeColumnsToContents()
    tabel.resizeRowsToContents()
    h = tabel.horizontalHeader().height() + 4
    for i in range(tabel.rowCount()):
        h += tabel.rowHeight(i)
    tabel.setFixedHeight(h)
    return tabel


def _geen_data_label() -> QLabel:
    lbl = QLabel('— geen data —')
    lbl.setStyleSheet(
        f'font-family: {_FONT}; font-size: 11px; color: #7a93a8; padding: 4px 12px;'
    )
    return lbl


# ── Rij-helpers ───────────────────────────────────────────────────────────────

def _anchor_rij(a: Anchor) -> list[str]:
    return [str(a.nr), a.name, str(a.level), str(a.emod), str(a.cross_section),
            str(a.length), str(a.yield_f), str(a.angle), str(a.height), str(a.side)]


def _strut_rij(s: Strut) -> list[str]:
    return [str(s.nr), s.name, str(s.level), str(s.emod), str(s.cross_section),
            str(s.length), str(s.yield_f), str(s.angle), str(s.aux), str(s.side)]


def _spring_rij(s: SpringSupport) -> list[str]:
    return [str(s.nr), s.name, str(s.level), str(s.rot_stiff), str(s.tr_stiff)]


def _rigid_rij(r: RigidSupport) -> list[str]:
    return [str(r.nr), r.name, str(r.level), str(r.rot_stiff), str(r.tr_stiff)]


def _uniform_rij(u: UniformLoad) -> list[str]:
    return [u.name, str(u.left), str(u.right), str(u.permanent), str(u.favourable)]


def _surcharge_rijen(s: SurchargeLoad) -> list[list[str]]:
    return [[str(p['distance']), str(p['value'])] for p in s.points]


def _lijnlast_rij(h: HorizontalLineLoad) -> list[str]:
    return [str(h.nr), h.name, str(h.level), str(h.value),
            str(h.permanent), str(h.favourable)]


def _moment_rij(m: Moment) -> list[str]:
    return [str(m.nr), m.name, str(m.level), str(m.value),
            str(m.permanent), str(m.favourable)]


def _normaal_rij(n: NormalForce) -> list[str]:
    return [str(n.nr), n.name, str(n.top), str(n.surface_left),
            str(n.surface_right), str(n.bottom), str(n.permanent), str(n.favourable)]


def _niet_gevonden(naam: str, hdrs: list[str]) -> list[str]:
    kolom = hdrs.index('name') if 'name' in hdrs else 0
    rij = ['—'] * len(hdrs)
    rij[kolom] = f'NIET GEVONDEN: {naam}'
    return rij


class TabDebugInvoer(QWidget):
    """Toont alle geparste invoerdata van het actieve project als scrollbare sectielijst."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(4)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def update_project(self, project: Project | None) -> None:
        """Ververs de tabelweergave voor het opgegeven project.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        self._project = project
        self._herbouw()

    # ------------------------------------------------------------------
    # Interne opbouw
    # ------------------------------------------------------------------

    def _herbouw(self) -> None:
        self._leeg_content()
        if not self._project:
            lbl = QLabel('Geen project geladen.')
            lbl.setStyleSheet(
                f'font-family: {_FONT}; color: #7a93a8; font-size: 13px; padding: 32px;'
            )
            self._voeg_in(lbl)
            return

        p = self._project

        # 1 – PROJECT
        self._voeg_in(_maak_header('PROJECT'))
        self._voeg_in(_maak_tabel(['veld', 'waarde'], [
            ['base_name', p.base_name],
            ['project_name', p.project_name],
        ]))

        # 2 – DAMWANDELEMENTEN
        self._voeg_in(_maak_header('DAMWANDELEMENTEN'))
        if p.sheet_piling:
            hdrs = ['name', 'x', 'bottom', 'top', 'width', 'segment_top',
                    'segment_bottom', 'height_mm', 'pile_width_mm', 'EI [kNm²/m]',
                    'A [cm²/m]', 'Wres [cm³/m]', 'Mkar [kNm/m]', 'Mopn [kNm/m]', 'staalsoort']
            rijen = [[
                e.name, str(e.x), str(e.bottom), str(e.top), str(e.width),
                str(e.segment_top), str(e.segment_bottom), str(e.height_mm),
                str(e.pile_width_mm), str(e.ei_knm2_per_m), str(e.section_area_cm2),
                str(e.resisting_moment_cm3), str(e.max_char_moment_knm),
                str(e.opneembaar_moment_knm), e.steel_quality,
            ] for e in p.sheet_piling]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 3 – WATERPEILEN
        self._voeg_in(_maak_header('WATERPEILEN'))
        if p.waterlevels:
            self._voeg_in(_maak_tabel(
                ['name', 'level [m NAP]'],
                [[w.name, str(w.level)] for w in p.waterlevels],
            ))
        else:
            self._voeg_in(_geen_data_label())

        # 4 – GRONDSOORTEN
        self._voeg_in(_maak_header('GRONDSOORTEN'))
        if p.soils:
            hdrs = ['name', 'kleur', 'γd', 'γn', "c'", 'φ', 'δ', 'kh1', 'kh2', 'kh3']
            rijen = [[
                s.name, s.color, str(s.gamma_dry), str(s.gamma_wet),
                str(s.cohesion), str(s.phi), str(s.delta),
                str(s.kh1), str(s.kh2), str(s.kh3),
            ] for s in p.soils]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 5 – GRONDPROFIELEN
        self._voeg_in(_maak_header('GRONDPROFIELEN'))
        if p.profiles:
            for profiel in p.profiles:
                self._voeg_in(_maak_subheader(
                    f'{profiel.name}  '
                    f'(normalized: {profiel.normalized_name}, x={profiel.x}, y={profiel.y})'
                ))
                if profiel.layers:
                    self._voeg_in(_maak_tabel(
                        ['nr', 'level', 'wosp_top', 'wosp_bottom', 'material'],
                        [[str(l.nr), str(l.level), str(l.wosp_top),
                          str(l.wosp_bottom), l.material]
                         for l in profiel.layers],
                    ))
                else:
                    self._voeg_in(_geen_data_label())
        else:
            self._voeg_in(_geen_data_label())

        # 6 – MAAIVELDLIJNEN
        self._voeg_in(_maak_header('MAAIVELDLIJNEN'))
        if p.surfaces:
            for surf in p.surfaces:
                self._voeg_in(_maak_subheader(f'{surf.name}  (nr={surf.nr})'))
                if surf.points:
                    self._voeg_in(_maak_tabel(
                        ['nr', 'x', 'y'],
                        [[str(pt['nr']), str(pt['x']), str(pt['y'])]
                         for pt in surf.points],
                    ))
                else:
                    self._voeg_in(_geen_data_label())
        else:
            self._voeg_in(_geen_data_label())

        # 7 – ANKERS
        self._voeg_in(_maak_header('ANKERS'))
        if p.anchors:
            self._voeg_in(_maak_tabel(_ANCHOR_HDRS, [_anchor_rij(a) for a in p.anchors]))
        else:
            self._voeg_in(_geen_data_label())

        # 8 – STEMPELS
        self._voeg_in(_maak_header('STEMPELS'))
        if p.struts:
            self._voeg_in(_maak_tabel(_STRUT_HDRS, [_strut_rij(s) for s in p.struts]))
        else:
            self._voeg_in(_geen_data_label())

        # 9 – VERINGSSTEUNEN
        self._voeg_in(_maak_header('VERINGSSTEUNEN'))
        if p.spring_supports:
            self._voeg_in(_maak_tabel(_SPRING_HDRS, [_spring_rij(s) for s in p.spring_supports]))
        else:
            self._voeg_in(_geen_data_label())

        # 10 – STIJVE STEUNEN
        self._voeg_in(_maak_header('STIJVE STEUNEN'))
        if p.rigid_supports:
            self._voeg_in(_maak_tabel(_RIGID_HDRS, [_rigid_rij(r) for r in p.rigid_supports]))
        else:
            self._voeg_in(_geen_data_label())

        # 11 – GELIJKMATIGE BELASTINGEN
        self._voeg_in(_maak_header('GELIJKMATIGE BELASTINGEN'))
        if p.uniform_loads:
            self._voeg_in(_maak_tabel(_UNIFORM_HDRS, [_uniform_rij(u) for u in p.uniform_loads]))
        else:
            self._voeg_in(_geen_data_label())

        # 12 – LIJNBELASTINGEN
        self._voeg_in(_maak_header('LIJNBELASTINGEN'))
        if p.horizontal_line_loads:
            self._voeg_in(_maak_tabel(
                _LIJNLAST_HDRS,
                [_lijnlast_rij(h) for h in p.horizontal_line_loads],
            ))
        else:
            self._voeg_in(_geen_data_label())

        # 13 – MAAIVELDBELASTINGEN
        self._voeg_in(_maak_header('MAAIVELDBELASTINGEN'))
        if p.surcharge_loads:
            for belasting in p.surcharge_loads:
                self._voeg_in(_maak_subheader(belasting.name))
                if belasting.points:
                    self._voeg_in(_maak_tabel(_SURCHARGE_HDRS, _surcharge_rijen(belasting)))
                else:
                    self._voeg_in(_geen_data_label())
        else:
            self._voeg_in(_geen_data_label())

        # 14 – MOMENTEN
        self._voeg_in(_maak_header('MOMENTEN'))
        if p.moments:
            self._voeg_in(_maak_tabel(_MOMENT_HDRS, [_moment_rij(m) for m in p.moments]))
        else:
            self._voeg_in(_geen_data_label())

        # 15 – NORMAALKRACHTEN
        self._voeg_in(_maak_header('NORMAALKRACHTEN'))
        if p.normal_forces:
            self._voeg_in(_maak_tabel(_NORMAAL_HDRS, [_normaal_rij(n) for n in p.normal_forces]))
        else:
            self._voeg_in(_geen_data_label())

        # 16 – FASES (opgelost per fase)
        for stage in p.stages:
            self._render_fase(stage, p)

    def _render_fase(self, stage: Stage, p: Project) -> None:
        """Render één bouwfase met volledig opgeloste objectdata."""
        self._voeg_in(_maak_header(f'FASE: {stage.name}'))

        # Basisvelden als key-value tabel
        self._voeg_in(_maak_tabel(['veld', 'waarde'], [
            ['method_line',   stage.method_line],
            ['left_surface',  stage.left_surface],
            ['right_surface', stage.right_surface],
            ['left_water',    stage.left_water],
            ['right_water',   stage.right_water],
            ['left_profile',  stage.left_profile],
            ['right_profile', stage.right_profile],
        ]))

        if stage.anchors:
            self._voeg_in(_maak_subheader('Ankers'))
            rijen = [
                _anchor_rij(a) if (a := _find(p.anchors, naam))
                else _niet_gevonden(naam, _ANCHOR_HDRS)
                for naam in stage.anchors
            ]
            self._voeg_in(_maak_tabel(_ANCHOR_HDRS, rijen))

        if stage.struts:
            self._voeg_in(_maak_subheader('Stempels'))
            rijen = [
                _strut_rij(s) if (s := _find(p.struts, naam))
                else _niet_gevonden(naam, _STRUT_HDRS)
                for naam in stage.struts
            ]
            self._voeg_in(_maak_tabel(_STRUT_HDRS, rijen))

        if stage.spring_supports:
            self._voeg_in(_maak_subheader('Veringssteunen'))
            rijen = [
                _spring_rij(s) if (s := _find(p.spring_supports, naam))
                else _niet_gevonden(naam, _SPRING_HDRS)
                for naam in stage.spring_supports
            ]
            self._voeg_in(_maak_tabel(_SPRING_HDRS, rijen))

        if stage.rigid_supports:
            self._voeg_in(_maak_subheader('Stijve steunen'))
            rijen = [
                _rigid_rij(r) if (r := _find(p.rigid_supports, naam))
                else _niet_gevonden(naam, _RIGID_HDRS)
                for naam in stage.rigid_supports
            ]
            self._voeg_in(_maak_tabel(_RIGID_HDRS, rijen))

        if stage.uniform_loads:
            self._voeg_in(_maak_subheader('Gelijkmatige belastingen'))
            rijen = [
                _uniform_rij(u) if (u := _find(p.uniform_loads, naam))
                else _niet_gevonden(naam, _UNIFORM_HDRS)
                for naam in stage.uniform_loads
            ]
            self._voeg_in(_maak_tabel(_UNIFORM_HDRS, rijen))

        if stage.surcharge_loads:
            self._voeg_in(_maak_subheader('Maaiveldbelastingen (gecombineerd)'))
            for naam in stage.surcharge_loads:
                sl = _find(p.surcharge_loads, naam)
                self._voeg_in(_maak_subheader(f'  {naam}'))
                if sl and sl.points:
                    self._voeg_in(_maak_tabel(_SURCHARGE_HDRS, _surcharge_rijen(sl)))
                else:
                    self._voeg_in(_geen_data_label())

        if stage.surcharge_loads_left:
            self._voeg_in(_maak_subheader('Maaiveldbelastingen links'))
            for naam in stage.surcharge_loads_left:
                sl = _find(p.surcharge_loads, naam)
                self._voeg_in(_maak_subheader(f'  {naam}'))
                if sl and sl.points:
                    self._voeg_in(_maak_tabel(_SURCHARGE_HDRS, _surcharge_rijen(sl)))
                else:
                    self._voeg_in(_geen_data_label())

        if stage.surcharge_loads_right:
            self._voeg_in(_maak_subheader('Maaiveldbelastingen rechts'))
            for naam in stage.surcharge_loads_right:
                sl = _find(p.surcharge_loads, naam)
                self._voeg_in(_maak_subheader(f'  {naam}'))
                if sl and sl.points:
                    self._voeg_in(_maak_tabel(_SURCHARGE_HDRS, _surcharge_rijen(sl)))
                else:
                    self._voeg_in(_geen_data_label())

        if stage.horizontal_line_loads:
            self._voeg_in(_maak_subheader('Lijnbelastingen'))
            rijen = [
                _lijnlast_rij(h) if (h := _find(p.horizontal_line_loads, naam))
                else _niet_gevonden(naam, _LIJNLAST_HDRS)
                for naam in stage.horizontal_line_loads
            ]
            self._voeg_in(_maak_tabel(_LIJNLAST_HDRS, rijen))

        if stage.moments:
            self._voeg_in(_maak_subheader('Momenten'))
            rijen = [
                _moment_rij(m) if (m := _find(p.moments, naam))
                else _niet_gevonden(naam, _MOMENT_HDRS)
                for naam in stage.moments
            ]
            self._voeg_in(_maak_tabel(_MOMENT_HDRS, rijen))

        if stage.normal_forces:
            self._voeg_in(_maak_subheader('Normaalkrachten'))
            rijen = [
                _normaal_rij(n) if (n := _find(p.normal_forces, naam))
                else _niet_gevonden(naam, _NORMAAL_HDRS)
                for naam in stage.normal_forces
            ]
            self._voeg_in(_maak_tabel(_NORMAAL_HDRS, rijen))

    def _voeg_in(self, widget: QWidget) -> None:
        self._content_layout.insertWidget(self._content_layout.count() - 1, widget)

    def _leeg_content(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
