"""Tab 3B — Resultaatbeschrijving: gegenereerde tekst + maatgevende resultaattabel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGroupBox, QComboBox, QGridLayout, QSizePolicy,
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
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar met fase-combo
        toolbar = QWidget()
        toolbar.setStyleSheet(f'background: {_HDR_BG};')
        tb_lay = QHBoxLayout(toolbar)
        tb_lay.setContentsMargins(12, 8, 12, 8)
        tb_lay.setSpacing(8)

        lbl = QLabel('Fase:')
        lbl.setStyleSheet(
            f'color: {_HDR_FG}; font-family: {_FONT}; font-size: 13px; font-weight: 600;'
        )
        tb_lay.addWidget(lbl)

        self._fase_combo = QComboBox()
        self._fase_combo.setMinimumWidth(200)
        self._fase_combo.setStyleSheet(
            'QComboBox { background: white; color: #1b3a5c; '
            'border: 1px solid #c4d4e0; border-radius: 4px; padding: 4px 8px; font-size: 12px; }'
        )
        tb_lay.addWidget(self._fase_combo)
        tb_lay.addStretch()

        root.addWidget(toolbar)

        # Scrollgebied
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f'QScrollArea {{ background: {_SCROLL_BG}; border: none; }}')

        self._content = QWidget()
        self._content.setStyleSheet(f'background: {_SCROLL_BG};')
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(16, 16, 16, 16)
        self._main_layout.setSpacing(12)
        self._main_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

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
            for field in sec.fields:
                val = f'{field.value} {field.unit}'.strip() if field.unit else field.value
                vl.addWidget(QLabel(f'<b>{field.label}:</b> {val}'))
            for table in sec.tables:
                vl.addWidget(QLabel(f'<b>{table.title}</b>'))
                header = ' | '.join(table.columns)
                vl.addWidget(QLabel(f'<i>{header}</i>'))
                for row in table.rows:
                    vl.addWidget(QLabel('  ' + ' | '.join(row)))
            self._main_layout.insertWidget(self._main_layout.count() - 1, box)

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

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

        for nr, (naam, kracht, niveau) in enumerate(summary.ondersteuningen[:4], start=1):
            rijen.append((f'Ondersteuning {nr}', naam, '[kN/m]'))
            rijen.append((f'Niveau ondersteuning {nr}', fmt_number(niveau), '[m NAP]'))

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
