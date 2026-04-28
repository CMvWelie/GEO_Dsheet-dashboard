"""Tab 3B — Resultaatbeschrijving: gegenereerde tekst + maatgevende resultaattabel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGroupBox, QComboBox, QGridLayout, QSizePolicy, QTabWidget,
)
from PyQt6.QtCore import Qt

from parsers.models import Project, ResultSummary
from reporting.models import ReportSection
from utils.formatting import fmt_number

_HDR_BG     = '#1b3a5c'
_HDR_FG     = '#ffffff'
_BORDER     = '#c4d4e0'
_ROW_SEP    = '#dce8f0'
_ROW_ODD_BG = '#f3f8fc'
_ROW_EVN_BG = '#ffffff'
_LABEL_CLR  = '#2c3f52'
_VALUE_CLR  = '#0f1e2b'
_EXTRA_CLR  = '#2171ae'
_SCROLL_BG  = '#e8eef3'
_FONT       = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'


class TabResultDesc(QWidget):
    """Toont resultaattabel en gegenereerde resultaatbeschrijvingen (Tab 3B)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._tabel_widget: QWidget | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Fase-keuze
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        ctrl_row.addWidget(QLabel('Fase:'))

        self._fase_combo = QComboBox()
        self._fase_combo.setMinimumWidth(200)
        ctrl_row.addWidget(self._fase_combo)
        ctrl_row.addStretch()

        root.addLayout(ctrl_row)

        # Scrollgebied
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(12)
        self._main_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll, stretch=1)

        self._fase_combo.currentIndexChanged.connect(self._on_fase_changed)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate_resultaat_tabel(self, project: Project | None) -> None:
        """Vul de fase-combo en render de resultaattabel voor de eerste fase."""
        self._project = project
        self._fase_combo.blockSignals(True)
        self._fase_combo.clear()

        if not project or not project.result_summaries:
            self._fase_combo.blockSignals(False)
            self._clear_tabel()
            return

        for summary in project.result_summaries:
            label = f'Fase {summary.stage_number}'
            if summary.stage_number <= len(project.stages):
                label = project.stages[summary.stage_number - 1].name
            self._fase_combo.addItem(label)

        self._fase_combo.blockSignals(False)
        self._render_tabel(0)

    def populate(self, sections: list[ReportSection]) -> None:
        """Voeg gegenereerde tekstsecties toe (bestaande API, ongewijzigd)."""
        # Verwijder alleen de tekstsecties (GroupBox-widgets), niet de resultaattabel
        verwijder = []
        for i in range(self._main_layout.count()):
            widget = self._main_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                verwijder.append(widget)
        for w in verwijder:
            w.deleteLater()

        if not sections:
            return

        for sec in sections:
            box = QGroupBox(sec.title)
            box.setStyleSheet(
                'QGroupBox { background: white; border: 1px solid #cfd6dd; '
                'border-radius: 8px; margin-top: 4px; padding: 4px; font-weight: bold; } '
                'QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }'
            )
            vl = QVBoxLayout(box)
            vl.setContentsMargins(0, 4, 0, 0)
            vl.setSpacing(6)
            for field in sec.fields:
                val = f'{field.value} {field.unit}'.strip() if field.unit else field.value
                lbl = QLabel(f'<b>{field.label}:</b> {val}')
                lbl.setStyleSheet('padding: 0 8px;')
                vl.addWidget(lbl)
            if len(sec.tables) > 1:
                tabs = QTabWidget()
                tabs.setDocumentMode(True)
                for table in sec.tables:
                    tabs.addTab(self._maak_styled_tabel(table), table.title)
                vl.addWidget(tabs)
            else:
                for table in sec.tables:
                    vl.addWidget(self._maak_styled_tabel(table))
            self._main_layout.insertWidget(self._main_layout.count() - 1, box)

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _maak_styled_tabel(self, table) -> QWidget:
        """Rendert een ReportTable als gestijlde grid-tabel.

        Ondersteunt optioneel een groepkop-rij (rij 0) wanneer
        table.column_groups gevuld is; kolomkoppen komen dan op rij 1.
        """
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        buitenste = QHBoxLayout(wrapper)
        buitenste.setContentsMargins(0, 0, 0, 0)
        buitenste.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame)
        buitenste.addStretch()

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n_cols = len(table.columns)
        heeft_groepen = bool(table.column_groups)
        kop_rij = 1 if heeft_groepen else 0
        data_start = kop_rij + 1

        # Groepkoppen (grid-rij 0) — alleen als column_groups gevuld is
        if heeft_groepen:
            col_offset = 0
            for groep_label, colspan in table.column_groups:
                lbl = QLabel(groep_label)
                lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                groep_bg = _HDR_BG if not groep_label else '#274f77'
                border_r = ('border-right: 1px solid #1d4568;'
                             if col_offset + colspan < n_cols else '')
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 10px; font-weight: 700; '
                    f'color: {_HDR_FG}; background: {groep_bg}; '
                    f'padding: 5px 10px; {border_r}'
                )
                grid.addWidget(lbl, 0, col_offset, 1, colspan)
                col_offset += colspan

        # Kolomkoppen (grid-rij kop_rij)
        for col, kop in enumerate(table.columns):
            lbl = QLabel(kop)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = 'border-right: 1px solid #1d4568;' if col < n_cols - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: #b8d4ea; background: {_HDR_BG}; '
                f'padding: 6px 10px; {border_r}'
            )
            grid.addWidget(lbl, kop_rij, col)

        # Datarijen (grid-rij data_start+)
        for row_i, rij in enumerate(table.rows):
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVN_BG
            is_last = row_i == len(table.rows) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            for col, cel in enumerate(rij):
                uitlijning = (Qt.AlignmentFlag.AlignLeft if col == 0
                              else Qt.AlignmentFlag.AlignRight)
                cel_lbl = QLabel(cel)
                cel_lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                border_r = (f'border-right: 1px solid {_ROW_SEP};'
                             if col < n_cols - 1 else '')
                cel_lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 10px; {border_r} {border_b}'
                )
                grid.addWidget(cel_lbl, data_start + row_i, col)

        return wrapper

    def _on_fase_changed(self, index: int) -> None:
        self._render_tabel(index)

    def _clear_tabel(self) -> None:
        """Verwijder de resultaattabel-widget als die bestaat."""
        if self._tabel_widget is not None:
            self._tabel_widget.deleteLater()
            self._tabel_widget = None

    def _render_tabel(self, index: int) -> None:
        self._clear_tabel()
        if not self._project or index < 0 or index >= len(self._project.result_summaries):
            return
        summary = self._project.result_summaries[index]
        self._tabel_widget = self._maak_tabel(summary)
        self._main_layout.insertWidget(0, self._tabel_widget)

    def _maak_tabel(self, summary: ResultSummary) -> QWidget:
        """Bouw de resultaattabel conform de spec."""
        project = self._project
        el = project.sheet_piling[0] if project and project.sheet_piling else None

        rijen: list[tuple[str, str, str]] = []

        # Damwandsectie
        rijen.append(('Damwand', '', ''))
        rijen.append(('Profiel', el.name.split('(')[0].strip() if el else '-', '[-]'))
        rijen.append(('Staalkwaliteit', el.steel_quality if el else '-', '[-]'))
        rijen.append(('Opneembaar moment', fmt_number(el.opneembaar_moment_knm) if el else '-', '[kNm/m]'))
        rijen.append(('Niveau damwand b.k.', fmt_number(el.top or 0.0) if el else '-', '[m NAP]'))
        rijen.append(('Niveau damwand o.k.', fmt_number(el.bottom) if el else '-', '[m NAP]'))
        rijen.append(('Damwandlengte', fmt_number(abs((el.top or 0.0) - el.bottom)) if el else '-', '[m]'))

        # Resultaten
        rijen.append(('Resultaten', '', ''))
        rijen.append(('Moment Msd', fmt_number(summary.max_moment_knm), '[kNm/m]'))
        rijen.append(('Dwarskracht Dsd', fmt_number(summary.max_shear_kn), '[kN/m]'))
        rijen.append(('Gemobiliseerd Moment', fmt_number(summary.mob_moment_pct), '[%]'))
        rijen.append(('Gemobiliseerd Grond', fmt_number(summary.mob_grond_pct), '[%]'))
        rijen.append(('Verplaatsing urep BGT', fmt_number(summary.max_disp_mm), '[mm]'))

        for naam, kracht, niveau in summary.ondersteuningen[:4]:
            rijen.append((naam, fmt_number(kracht), '[kN/m]'))
            rijen.append((f'Niveau {naam}', fmt_number(niveau), '[m NAP]'))

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        titel = QLabel('Specificaties')
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        lay.addWidget(titel)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnMinimumWidth(0, 220)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 100)

        for i, (label, waarde, eenheid) in enumerate(rijen):
            is_sectie = waarde == '' and eenheid == ''
            bg = _HDR_BG if is_sectie else (_ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG)
            is_last = i == len(rijen) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            fg = _HDR_FG if is_sectie else _LABEL_CLR

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {"12px" if not is_sectie else "11px"}; '
                f'font-weight: {"700" if is_sectie else "500"}; color: {fg}; '
                f'background: {bg}; padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP if not is_sectie else _HDR_BG}; {border_b}'
            )
            grid.addWidget(lbl, i, 0)

            if not is_sectie:
                val = QLabel(waarde)
                val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                val.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 14px; '
                    f'border-right: 1px solid {_ROW_SEP}; {border_b}'
                )
                grid.addWidget(val, i, 1)

                ext = QLabel(eenheid)
                ext.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                    f'color: {_EXTRA_CLR}; background: {bg}; padding: 6px 10px; {border_b}'
                )
                grid.addWidget(ext, i, 2)

        lay.addWidget(grid_w)
        return frame
