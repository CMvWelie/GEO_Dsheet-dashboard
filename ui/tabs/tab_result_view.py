"""Tab 3A — Resultaatweergave: momenten, dwarskrachten, vervormingen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSlider, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTabBar

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


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

        # ── Canvas ───────────────────────────────────────────────────
        self.results_fig = Figure(figsize=(14, 6), dpi=96)
        self.results_canvas = FigureCanvas(self.results_fig)
        self.results_canvas.setMinimumHeight(380)
        self.results_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.results_canvas, stretch=1)

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
