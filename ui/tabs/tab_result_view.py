"""Tab 3A — Resultaatweergave: momenten, dwarskrachten, vervormingen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSlider, QFrame,
    QScrollArea, QTabWidget, QGridLayout, QSplitter,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTabBar

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from reporting.models import ReportSection, ReportTable
from ui.table_styles import (
    TABLE_BORDER, TABLE_FONT, TABLE_HEADER_BG, TABLE_HEADER_FG,
    TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG, TABLE_ROW_EVEN_BG,
    TABLE_ROW_ODD_BG, TABLE_ROW_SEP, TABLE_HEADER_SIZE, TABLE_TEXT_SIZE,
    TABLE_VALUE_COLOR,
)

_HDR_BG     = TABLE_HEADER_BG
_HDR_FG     = TABLE_HEADER_FG
_SUBHDR_BG  = TABLE_HEADER_SUB_BG
_SUBHDR_FG  = TABLE_HEADER_SUB_FG
_BORDER     = TABLE_BORDER
_ROW_SEP    = TABLE_ROW_SEP
_ROW_ODD_BG = TABLE_ROW_ODD_BG
_ROW_EVN_BG = TABLE_ROW_EVEN_BG
_VALUE_CLR  = TABLE_VALUE_COLOR
_FONT       = TABLE_FONT
_HDR_PT     = TABLE_HEADER_SIZE
_DATA_PT    = TABLE_TEXT_SIZE
_MIN_H      = 27
_TBL_STRETCH     = 10
_TBL_REST_STRETCH = 6

_SECTIE_TOELICHTING: dict[str, str] = {
    'anchor_forces': (
        'Per fase de berekende anker- en stempelkrachten voor de aanwezige CUR 166-toetsstappen.'
    ),
    'per_phase_summary': (
        'Maximale absolute waarden per fase, uitgesplitst naar de beschikbare toetsstappen.'
    ),
}


def _scheidingslijn() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet('color: #aabdca; margin: 0px; max-height: 1px;')
    return line


class TabResultView(QWidget):
    """Resultaatgrafieken tab (Tab 3A).

    Exposeert attributen die MainWindow hergebruikt:
        output_stage_tabs, result_step_tabs, results_fig, results_canvas

    Parameters
    ----------
    parent : QWidget | None
        Optionele parent-widget.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step_keys: list[str] = []
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 4)
        root.setSpacing(0)

        # ── Rij 1: fase-tabbladen ────────────────────────────────────
        fase_rij = QWidget()
        fase_layout = QHBoxLayout(fase_rij)
        fase_layout.setContentsMargins(0, 0, 0, 0)
        fase_layout.setSpacing(8)
        lbl_fase = QLabel('Uitvoerfase:')
        lbl_fase.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        fase_layout.addWidget(lbl_fase)
        self.output_stage_tabs = QTabBar()
        self.output_stage_tabs.setExpanding(False)
        self.output_stage_tabs.setUsesScrollButtons(False)
        self.output_stage_tabs.addTab('Geen fase')
        fase_layout.addWidget(self.output_stage_tabs)
        fase_layout.addStretch()
        root.addWidget(fase_rij)

        root.addWidget(_scheidingslijn())

        # ── Rij 2: verificatiestap-tabbladen ─────────────────────────
        stap_rij = QWidget()
        stap_layout = QHBoxLayout(stap_rij)
        stap_layout.setContentsMargins(0, 2, 0, 0)
        stap_layout.setSpacing(8)
        lbl_stap = QLabel('Verificatiestap:')
        lbl_stap.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        stap_layout.addWidget(lbl_stap)
        self.result_step_tabs = QTabBar()
        self.result_step_tabs.setExpanding(False)
        self.result_step_tabs.setUsesScrollButtons(False)
        stap_layout.addWidget(self.result_step_tabs)
        stap_layout.addStretch()
        root.addWidget(stap_rij)

        root.addSpacing(4)

        # ── Breedteslider ────────────────────────────────────────────
        breedte_row = QWidget()
        bl = QHBoxLayout(breedte_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)
        bl.addWidget(QLabel('Zichtbare breedte:'))
        self.breedte_slider = QSlider(Qt.Orientation.Horizontal)
        self.breedte_slider.setRange(2, 60)
        self.breedte_slider.setValue(20)
        self.breedte_slider.setFixedWidth(220)
        self.breedte_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        bl.addWidget(self.breedte_slider)
        self._breedte_lbl = QLabel('20 m')
        self._breedte_lbl.setMinimumWidth(40)
        bl.addWidget(self._breedte_lbl)
        bl.addStretch()
        self.breedte_slider.valueChanged.connect(
            lambda v: self._breedte_lbl.setText(f'{v} m')
        )
        root.addWidget(breedte_row)

        # ── Splitter: canvas boven, tabellen scroll onder ─────────────
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setChildrenCollapsible(True)
        self._splitter.setHandleWidth(6)
        self._splitter.setStyleSheet(
            'QSplitter::handle { background: #cfd6dd; border-top: 1px solid #b0bec5; }'
            'QSplitter::handle:hover { background: #90a4ae; }'
        )

        self.results_fig = Figure(figsize=(14, 6), dpi=96)
        self.results_canvas = FigureCanvas(self.results_fig)
        self.results_canvas.setMinimumHeight(120)
        self.results_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._splitter.addWidget(self.results_canvas)

        self._tabel_scroll = QScrollArea()
        self._tabel_scroll.setWidgetResizable(True)
        self._tabel_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._tabel_content = QWidget()
        self._tabel_layout = QVBoxLayout(self._tabel_content)
        self._tabel_layout.setContentsMargins(0, 4, 0, 8)
        self._tabel_layout.setSpacing(8)
        self._tabel_layout.addStretch()
        self._tabel_scroll.setWidget(self._tabel_content)
        self._splitter.addWidget(self._tabel_scroll)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setSizes([600, 0])

        root.addWidget(self._splitter, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate_output_stages(self, namen: list[str]) -> None:
        """Vul de fase-tabbar met de opgegeven namen.

        Parameters
        ----------
        namen : list[str]
            Fasenamen in volgorde.
        """
        self.output_stage_tabs.blockSignals(True)
        while self.output_stage_tabs.count():
            self.output_stage_tabs.removeTab(0)
        for naam in namen:
            self.output_stage_tabs.addTab(naam)
        self.output_stage_tabs.blockSignals(False)

    def clear_output_stages(self) -> None:
        """Verwijder alle fase-tabbladen."""
        self.output_stage_tabs.blockSignals(True)
        while self.output_stage_tabs.count():
            self.output_stage_tabs.removeTab(0)
        self.output_stage_tabs.blockSignals(False)

    def populate_result_steps(self, keys: list[str], labels: list[str], actief: str | None = None) -> None:
        """Vul de verificatiestap-tabbar.

        Parameters
        ----------
        keys : list[str]
            Interne sleutelwaarden per stap.
        labels : list[str]
            Weergavenamen per stap (zelfde volgorde als keys).
        actief : str | None
            Optioneel: de key die actief geselecteerd moet zijn.
        """
        self._step_keys = list(keys)
        self.result_step_tabs.blockSignals(True)
        while self.result_step_tabs.count():
            self.result_step_tabs.removeTab(0)
        for label in labels:
            self.result_step_tabs.addTab(label)
        if actief and actief in self._step_keys:
            self.result_step_tabs.setCurrentIndex(self._step_keys.index(actief))
        self.result_step_tabs.blockSignals(False)

    def clear_result_steps(self) -> None:
        """Verwijder alle verificatiestap-tabbladen."""
        self._step_keys = []
        self.result_step_tabs.blockSignals(True)
        while self.result_step_tabs.count():
            self.result_step_tabs.removeTab(0)
        self.result_step_tabs.blockSignals(False)

    def current_result_step_key(self) -> str | None:
        """Geef de interne sleutel van de actief geselecteerde verificatiestap.

        Returns
        -------
        str | None
            Sleutelwaarde, of None als er geen stappen zijn.
        """
        idx = self.result_step_tabs.currentIndex()
        if 0 <= idx < len(self._step_keys):
            return self._step_keys[idx]
        return None

    def set_breedte(self, totale_breedte_m: float) -> None:
        """Stel de slider in vanuit opgeslagen RenderSettings (zonder signal cascade).

        Parameters
        ----------
        totale_breedte_m : float
            Gewenste totale breedte in meters.
        """
        waarde = max(2, min(60, round(totale_breedte_m)))
        self.breedte_slider.blockSignals(True)
        self.breedte_slider.setValue(waarde)
        self.breedte_slider.blockSignals(False)
        self._breedte_lbl.setText(f'{waarde} m')

    def populate_ondersteuning_tabellen(self, sections: list[ReportSection]) -> None:
        """Vul de tabelzone onder het canvas met anker- en fase-samenvattingstabellen.

        Parameters
        ----------
        sections:
            Resultaatbeschrijvingssecties; alleen anchor_forces en per_phase_summary
            worden weergegeven.
        """
        while self._tabel_layout.count() > 1:
            item = self._tabel_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        doelsecties = [s for s in sections if s.id in {'anchor_forces', 'per_phase_summary'}]
        if not doelsecties:
            self._splitter.setSizes([600, 0])
            return

        for sec in doelsecties:
            if not sec.tables:
                continue
            titel = QLabel(sec.title)
            titel.setStyleSheet(
                f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
                f'color: {_VALUE_CLR}; background: transparent; padding: 4px 4px 2px 4px;'
            )
            self._tabel_layout.insertWidget(self._tabel_layout.count() - 1, titel)

            toelichting = _SECTIE_TOELICHTING.get(sec.id)
            if toelichting:
                toel = QLabel(toelichting)
                toel.setWordWrap(True)
                toel.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: transparent; padding: 0px 4px 4px 4px;'
                )
                self._tabel_layout.insertWidget(self._tabel_layout.count() - 1, toel)

            gebruik_tabs = len(sec.tables) > 1 or (
                len(sec.tables) == 1 and bool(sec.tables[0].title)
            )
            if gebruik_tabs:
                tabs = QTabWidget()
                tabs.setDocumentMode(True)
                for table in sec.tables:
                    tabs.addTab(self._maak_styled_tabel(table), table.title)
                self._tabel_layout.insertWidget(self._tabel_layout.count() - 1, tabs)
            else:
                for table in sec.tables:
                    self._tabel_layout.insertWidget(
                        self._tabel_layout.count() - 1, self._maak_styled_tabel(table)
                    )

        total = self._splitter.height()
        tabel_h = min(240, max(120, total // 3))
        self._splitter.setSizes([total - tabel_h, tabel_h])

    # ------------------------------------------------------------------
    # Tabelrendering (identieke stijl als tab_result_desc)
    # ------------------------------------------------------------------

    def _maak_styled_tabel(self, table: ReportTable) -> QWidget:
        """Rendert een ReportTable als gestijlde grid-tabel."""
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        buitenste = QHBoxLayout(wrapper)
        buitenste.setContentsMargins(0, 0, 0, 0)
        buitenste.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame, stretch=_TBL_STRETCH)
        buitenste.addStretch(_TBL_REST_STRETCH)

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n_cols = len(table.columns)
        heeft_groepen = bool(table.column_groups)
        kop_rij = 1 if heeft_groepen else 0
        data_start = kop_rij + 1

        if heeft_groepen:
            col_offset = 0
            for groep_label, colspan in table.column_groups:
                lbl = QLabel(groep_label)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                groep_bg = _HDR_BG if not groep_label else _SUBHDR_BG
                border_r = (f'border-right: 1px solid {_BORDER};'
                             if col_offset + colspan < n_cols else '')
                lbl.setMinimumHeight(_MIN_H)
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                    f'color: {_HDR_FG}; background: {groep_bg}; '
                    f'padding: 3px 6px; min-height: {_MIN_H}px; {border_r}'
                )
                grid.addWidget(lbl, 0, col_offset, 1, colspan)
                col_offset += colspan

        for col, kop in enumerate(table.columns):
            lbl = QLabel(kop)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if col < n_cols - 1 else ''
            lbl.setMinimumHeight(_MIN_H)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_SUBHDR_FG}; background: {_HDR_BG}; '
                f'padding: 3px 6px; min-height: {_MIN_H}px; {border_r}'
            )
            grid.addWidget(lbl, kop_rij, col)

        for row_i, rij in enumerate(table.rows):
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVN_BG
            is_last = row_i == len(table.rows) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            for col, cel in enumerate(rij):
                uitlijning = (Qt.AlignmentFlag.AlignLeft if col == 0
                              else Qt.AlignmentFlag.AlignRight)
                cel_lbl = QLabel(str(cel))
                cel_lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                cel_lbl.setMinimumHeight(_MIN_H)
                border_r = (f'border-right: 1px solid {_ROW_SEP};'
                             if col < n_cols - 1 else '')
                cel_lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 2px 6px; '
                    f'min-height: {_MIN_H}px; {border_r} {border_b}'
                )
                grid.addWidget(cel_lbl, data_start + row_i, col)

        return wrapper
