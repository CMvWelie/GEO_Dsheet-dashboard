"""Tab Debug Uitvoer — toont geparste resultaatdata met collapsible grafiekpunten."""
from __future__ import annotations

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QPushButton,
)
from PyQt6.QtCore import Qt

from parsers.models import Project
from ui.table_styles import BASIC_DEBUG_QTABLE_STYLE

# ── Stijlconstanten (identiek aan tab_debug_invoer) ──────────────────────────
_FONT      = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
_HDR_BG    = '#1b3a5c'
_HDR_FG    = '#ffffff'
_SUBHDR_BG = '#274f77'


def _natural_sort_key(s: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def _maak_header(title: str) -> QLabel:
    lbl = QLabel(title)
    lbl.setStyleSheet(
        f'font-family: {_FONT}; font-size: 11px; font-weight: 700; '
        f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 6px 10px; margin-top: 8px;'
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
    tabel.setShowGrid(True)
    tabel.setProperty('debugTable', True)
    tabel.setStyleSheet(BASIC_DEBUG_QTABLE_STYLE)
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


class _CollapsibleSectie(QWidget):
    """Klikbare header met verborgen QTableWidget eronder."""

    def __init__(self, title: str, tabel: QTableWidget,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._tabel = tabel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        self._btn = QPushButton(f'▶  {title}')
        self._btn.setCheckable(True)
        self._btn.setChecked(False)
        self._btn.setStyleSheet(
            f'QPushButton {{ text-align: left; padding: 6px 10px; '
            f'font-family: {_FONT}; font-size: 11px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; border: none; }}'
            f'QPushButton:hover {{ background: {_SUBHDR_BG}; }}'
        )
        self._btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._btn.clicked.connect(self._toggle)

        self._tabel.hide()
        layout.addWidget(self._btn)
        layout.addWidget(self._tabel)

    def _toggle(self, checked: bool) -> None:
        self._tabel.setVisible(checked)
        prefix = '▼' if checked else '▶'
        self._btn.setText(f'{prefix}  {self._title}')


class TabDebugUitvoer(QWidget):
    """Toont geparste resultaatdata: samenvatting, resumés en collapsible grafiekpunten."""

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
        """Ververs de uitvoer-tabelweergave voor het opgegeven project.

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

        # 1 – OVERZICHT PER FASE EN STAP
        self._voeg_in(_maak_header('OVERZICHT PER FASE EN STAP'))
        if p.verify_step_summaries:
            hdrs = [
                'fase', 'stap', 'type',
                'max moment [kNm/m]', 'max dwarskracht [kN/m]',
                'max verplaatsing [mm]', 'mob. moment [%]', 'mob. grond [%]',
            ]
            gesorteerde_samenvattingen = sorted(
                p.verify_step_summaries,
                key=lambda vs: (vs.stage_number, _natural_sort_key(vs.step_label)),
            )
            rijen = [[
                str(vs.stage_number),
                vs.step_label,
                'UGT' if vs.is_ugt else 'BGT',
                str(vs.max_moment_knm),
                str(vs.max_shear_kn),
                '' if vs.max_disp_mm is None else str(vs.max_disp_mm),
                '' if vs.mob_moment_pct is None else str(vs.mob_moment_pct),
                '' if vs.mob_grond_pct is None else str(vs.mob_grond_pct),
            ] for vs in gesorteerde_samenvattingen]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 2 – RESULTAATSAMENVATTING (max per fase)
        self._voeg_in(_maak_header('RESULTAATSAMENVATTING (max per fase)'))
        if p.result_summaries:
            hdrs = ['fase', 'max moment [kNm/m]', 'max dwarskracht [kN/m]',
                    'max verplaatsing [mm]', 'mob. moment [%]', 'mob. grond [%]']
            rijen = [[
                str(rs.stage_number), str(rs.max_moment_knm), str(rs.max_shear_kn),
                str(rs.max_disp_mm), str(rs.mob_moment_pct), str(rs.mob_grond_pct),
            ] for rs in p.result_summaries]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 3 – ONDERSTEUNINGSKRACHTEN
        self._voeg_in(_maak_header('ONDERSTEUNINGSKRACHTEN'))
        ond_rijen: list[list[str]] = []
        for rs in p.result_summaries:
            for naam, kracht, niveau in rs.ondersteuningen:
                ond_rijen.append([str(rs.stage_number), naam, str(kracht), str(niveau)])
        if ond_rijen:
            self._voeg_in(_maak_tabel(
                ['fase', 'naam', 'kracht [kN/m]', 'niveau [m NAP]'],
                ond_rijen,
            ))
        else:
            self._voeg_in(_geen_data_label())

        # 4 – ANKER/STEMPEL RESUMÉ
        self._voeg_in(_maak_header('ANKER/STEMPEL RESUMÉ'))
        if p.anchor_strut_resume:
            hdrs = ['fase', 'naam', 'verificatietype', 'basis_cur_step',
                    'partial_factor_set', 'repr. factor', 'kracht [kN/m]',
                    'ankertype', 'ankerstatus', 'gewijzigd→vloeiend', 'rekenstatus']
            rijen = [[
                str(a.stage_number), a.name, str(a.verification_type),
                str(a.basis_cur_step), str(a.partial_factor_set),
                str(a.representative_factor), str(a.force),
                str(a.anchor_type), str(a.anchor_state),
                str(a.changed_to_yielding), str(a.calculation_status),
            ] for a in p.anchor_strut_resume]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 5 – STEUNEN RESUMÉ
        self._voeg_in(_maak_header('STEUNEN RESUMÉ'))
        if p.supports_resume:
            hdrs = ['fase', 'naam', 'verificatietype', 'basis_cur_step',
                    'partial_factor_set', 'repr. factor', 'kracht [kN/m]',
                    'moment [kNm/m]', 'steuntype', 'rekenstatus']
            rijen = [[
                str(s.stage_number), s.name, str(s.verification_type),
                str(s.basis_cur_step), str(s.partial_factor_set),
                str(s.representative_factor), str(s.force), str(s.moment),
                str(s.support_rigidity_type), str(s.calculation_status),
            ] for s in p.supports_resume]
            self._voeg_in(_maak_tabel(hdrs, rijen))
        else:
            self._voeg_in(_geen_data_label())

        # 6+ – GRAFIEKPUNTEN per rekenstap (collapsible, standaard ingeklapt)
        if p.result_steps:
            for stap_label, result_step in sorted(
                p.result_steps.items(), key=lambda kv: _natural_sort_key(kv[0])
            ):
                rijen = []
                for stage_nr in sorted(result_step.stages):
                    rs = result_step.stages[stage_nr]
                    for pt in rs.points:
                        rijen.append([
                            str(stage_nr), str(pt.depth), str(pt.moment),
                            str(pt.shear), str(pt.disp),
                        ])
                tabel = _maak_tabel(
                    ['fase', 'diepte [m NAP]', 'moment [kNm/m]',
                     'dwarskracht [kN/m]', 'verplaatsing [mm]'],
                    rijen,
                )
                self._voeg_in(_CollapsibleSectie(
                    f'GRAFIEKPUNTEN — {stap_label}', tabel
                ))
        else:
            self._voeg_in(_maak_header('GRAFIEKPUNTEN'))
            self._voeg_in(_geen_data_label())

    def _voeg_in(self, widget: QWidget) -> None:
        self._content_layout.insertWidget(self._content_layout.count() - 1, widget)

    def _leeg_content(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
