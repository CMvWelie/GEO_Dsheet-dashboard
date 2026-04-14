"""Tab 3A — Resultaatweergave: momenten, dwarskrachten, vervormingen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSizePolicy,
)

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class TabResultView(QWidget):
    """Resultaatgrafieken tab (Tab 3A).

    Exposeert attributen die MainWindow via aliassen hergebruikt:
        output_stage_combo, result_step_combo, results_fig, results_canvas
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Selectiebalk
        sel_row = QWidget()
        sl = QHBoxLayout(sel_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(QLabel('Uitvoerfase:'))
        self.output_stage_combo = QComboBox()
        self.output_stage_combo.setMinimumWidth(200)
        sl.addWidget(self.output_stage_combo)
        sl.addWidget(QLabel('Verificatiestap:'))
        self.result_step_combo = QComboBox()
        self.result_step_combo.setMinimumWidth(100)
        sl.addWidget(self.result_step_combo)
        sl.addStretch()
        root.addWidget(sel_row)

        # Canvas
        self.results_fig = Figure(figsize=(14, 6), dpi=96)
        self.results_canvas = FigureCanvas(self.results_fig)
        self.results_canvas.setMinimumHeight(380)
        self.results_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self.results_canvas, stretch=1)
