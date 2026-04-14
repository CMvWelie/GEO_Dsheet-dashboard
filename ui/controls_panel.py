"""Viewport- en renderschaalbediening."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QCheckBox, QDoubleSpinBox, QPushButton
)
from PyQt6.QtCore import pyqtSignal

from app.settings import RenderSettings, ViewportSettings


class ControlsPanel(QWidget):
    """Panel met viewport- en renderinstellingen.

    Signals
    -------
    viewport_changed:  Viewport-instellingen zijn gewijzigd.
    render_changed:    Render-instellingen zijn gewijzigd.
    zoom_in:           Zoom-in knop ingedrukt.
    zoom_out:          Zoom-out knop ingedrukt.
    zoom_reset:        Auto-reset knop ingedrukt.
    """

    viewport_changed = pyqtSignal(object)   # ViewportSettings
    render_changed = pyqtSignal(object)     # RenderSettings
    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    zoom_reset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # --- Viewport ---
        vp_box = QGroupBox('Viewport')
        vp_layout = QVBoxLayout(vp_box)

        self._auto_check = QCheckBox('Automatisch bereik')
        self._auto_check.setChecked(True)
        self._auto_check.toggled.connect(self._on_viewport_change)
        vp_layout.addWidget(self._auto_check)

        def _spin(lo=-9999.0, hi=9999.0, val=0.0, step=0.5) -> QDoubleSpinBox:
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            s.setSingleStep(step)
            s.setDecimals(1)
            return s

        for label_text, attr, default in [
            ('X min', '_xmin', -10.0), ('X max', '_xmax', 10.0),
            ('Y min', '_ymin', -10.0), ('Y max', '_ymax', 5.0),
        ]:
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(QLabel(label_text))
            spin = _spin(val=default)
            spin.valueChanged.connect(self._on_viewport_change)
            setattr(self, attr, spin)
            row_l.addWidget(spin)
            vp_layout.addWidget(row)

        zoom_row = QWidget()
        zoom_l = QHBoxLayout(zoom_row)
        zoom_l.setContentsMargins(0, 0, 0, 0)
        for label, signal in [('Zoom in', self.zoom_in),
                               ('Zoom uit', self.zoom_out),
                               ('Auto-reset', self.zoom_reset)]:
            btn = QPushButton(label)
            btn.clicked.connect(signal.emit)
            zoom_l.addWidget(btn)
        vp_layout.addWidget(zoom_row)
        layout.addWidget(vp_box)

        # --- Render instellingen ---
        rs_box = QGroupBox('Renderinstellingen')
        rs_layout = QVBoxLayout(rs_box)

        for label_text, attr, default, tooltip in [
            ('Uniform 10kPa = m', '_uni_scale', 0.5,
             'Hoogte belastingblok: m per 10 kPa'),
            ('Normaal 10kN/m = m', '_norm_scale', 0.5,
             'Breedte normaalkrachtdiagram: m per 10 kN/m'),
            ('H-last laag (m)', '_hload_low', 1.0, 'Lijnlast < 30 kN/m'),
            ('H-last midden (m)', '_hload_mid', 2.0, 'Lijnlast 30-60 kN/m'),
            ('H-last hoog (m)', '_hload_high', 3.0, 'Lijnlast > 60 kN/m'),
            ('Moment radius (m)', '_mom_radius', 1.0, 'Straal momentensymbool'),
        ]:
            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label_text)
            lbl.setToolTip(tooltip)
            row_l.addWidget(lbl)
            spin = _spin(lo=0.01, hi=100.0, val=default, step=0.1)
            spin.setToolTip(tooltip)
            spin.valueChanged.connect(self._on_render_change)
            setattr(self, attr, spin)
            row_l.addWidget(spin)
            rs_layout.addWidget(row)

        layout.addWidget(rs_box)
        layout.addStretch()

    def _on_viewport_change(self) -> None:
        self.viewport_changed.emit(self.get_viewport_settings())

    def _on_render_change(self) -> None:
        self.render_changed.emit(self.get_render_settings())

    def get_viewport_settings(self) -> ViewportSettings:
        """Lees de huidige viewport-instellingen uit de UI."""
        return ViewportSettings(
            auto=self._auto_check.isChecked(),
            x_min=self._xmin.value(),
            x_max=self._xmax.value(),
            y_min=self._ymin.value(),
            y_max=self._ymax.value(),
        )

    def get_render_settings(self) -> RenderSettings:
        """Lees de huidige render-instellingen uit de UI."""
        return RenderSettings(
            uniform_meters_per_10kpa=self._uni_scale.value(),
            normal_meters_per_10knm=self._norm_scale.value(),
            hload_low_scale=self._hload_low.value(),
            hload_mid_scale=self._hload_mid.value(),
            hload_high_scale=self._hload_high.value(),
            moment_radius_meters=self._mom_radius.value(),
        )

    def set_viewport(self, vp: ViewportSettings) -> None:
        """Vul de UI in vanuit een ViewportSettings object.

        Parameters
        ----------
        vp: Te tonen viewport-instellingen.
        """
        self._auto_check.blockSignals(True)
        self._auto_check.setChecked(vp.auto)
        self._auto_check.blockSignals(False)
        for spin, val in [(self._xmin, vp.x_min), (self._xmax, vp.x_max),
                           (self._ymin, vp.y_min), (self._ymax, vp.y_max)]:
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)
