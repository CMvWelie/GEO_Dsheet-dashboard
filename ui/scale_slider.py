"""ScaleSlider — compacte slider met instelbare min/max voor verschaalwaarden."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QSlider, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

_HDR_STYLE = 'font-size: 8px; color: #888; margin: 0; padding: 0;'
_HDR_STYLE_DISABLED = 'font-size: 8px; color: #c8cdd2; margin: 0; padding: 0;'
_NAME_STYLE = 'font-size: 10px; color: #2c3e50;'
_NAME_STYLE_DISABLED = 'font-size: 10px; color: #aab0b8;'
_VAL_STYLE = (
    'QDoubleSpinBox { font-size: 10px; font-weight: bold; color: #245b7a; '
    'background: #f0f5f9; border: 1px solid #aabdca; border-radius: 3px; '
    'padding: 1px 3px; }'
    'QDoubleSpinBox:focus { border-color: #245b7a; background: #ffffff; }'
    'QDoubleSpinBox:disabled { color: #aab0b8; background: #eef0f3; '
    'border-color: #d8dce0; }'
)
_MINMAX_STYLE = (
    'QDoubleSpinBox { font-size: 9px; }'
    'QDoubleSpinBox:disabled { color: #aab0b8; background: #eef0f3; }'
)
_SLIDER_DISABLED_STYLE = (
    'QSlider::groove:horizontal:disabled,'
    'QSlider::sub-page:horizontal:disabled,'
    'QSlider::add-page:horizontal:disabled { background: #d8dce0; }'
    'QSlider::handle:horizontal:disabled { background: #aab0b8; '
    'border: 2px solid #f0f5f9; }'
)


class ScaleSlider(QWidget):
    """Horizontale slider met instelbare min/max en waarde-display.

    Controle-rij:  [waarde] [min_spin] [slider] [max_spin]
    Header-rij (optioneel, alleen bovenste rij per sectie):
                   [       ] [  min  ] [       ] [  max  ]

    API compatibel met QDoubleSpinBox:
        .value(), .setValue(float), .valueChanged
    """

    valueChanged = pyqtSignal(float)

    _STEPS = 1000

    def __init__(
        self,
        label: str,
        lo: float,
        hi: float,
        default: float,
        decimals: int = 2,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._lo = lo
        self._hi = hi
        self._val = default
        self._decimals = decimals
        self._build(label, lo, hi, default)

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------

    def _build(self, label: str, lo: float, hi: float, default: float) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)
        root.setSpacing(0)

        # ── Naam-rij (verbergbaar in popup-modus) ────────────────────
        self._name_row = QWidget()
        name_hl = QHBoxLayout(self._name_row)
        name_hl.setContentsMargins(0, 0, 0, 0)
        self._name_lbl = QLabel(label)
        self._name_lbl.setStyleSheet(_NAME_STYLE)
        name_hl.addWidget(self._name_lbl)
        name_hl.addStretch()
        root.addWidget(self._name_row)

        # ── Grid: optionele header-rij + controle-rij ────────────────
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(3)
        self._grid.setVerticalSpacing(0)
        self._grid.setColumnStretch(2, 1)   # slider rekt mee

        # Header-rij: "min" boven col 1, "max" boven col 3
        self._min_hdr = QLabel('min')
        self._min_hdr.setStyleSheet(_HDR_STYLE)
        self._min_hdr.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._max_hdr = QLabel('max')
        self._max_hdr.setStyleSheet(_HDR_STYLE)
        self._max_hdr.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._grid.addWidget(self._min_hdr, 0, 1)
        self._grid.addWidget(self._max_hdr, 0, 3)

        # Controle-rij: val_spin | min_spin | slider | max_spin
        self._val_spin = QDoubleSpinBox()
        self._val_spin.setRange(lo, hi)
        self._val_spin.setValue(default)
        self._val_spin.setDecimals(self._decimals)
        self._val_spin.setFixedWidth(52)
        self._val_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self._val_spin.setStyleSheet(_VAL_STYLE)
        self._val_spin.valueChanged.connect(self._on_val_spin_changed)

        self._min_spin = self._make_spin(lo)
        self._min_spin.valueChanged.connect(self._on_min_changed)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, self._STEPS)
        self._slider.setValue(self._to_pos(default))
        self._slider.setStyleSheet(_SLIDER_DISABLED_STYLE)
        self._slider.valueChanged.connect(self._on_slider_moved)

        self._max_spin = self._make_spin(hi)
        self._max_spin.valueChanged.connect(self._on_max_changed)

        self._grid.addWidget(self._val_spin, 1, 0)
        self._grid.addWidget(self._min_spin, 1, 1)
        self._grid.addWidget(self._slider,   1, 2)
        self._grid.addWidget(self._max_spin, 1, 3)

        # Standaard headers verborgen; toon via set_header_visible(True)
        self._min_hdr.setVisible(False)
        self._max_hdr.setVisible(False)

        root.addLayout(self._grid)

    @staticmethod
    def _make_spin(val: float) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(-9999, 9999)
        s.setValue(val)
        s.setDecimals(2)
        s.setFixedWidth(52)
        s.setStyleSheet(_MINMAX_STYLE)
        s.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        return s

    # ------------------------------------------------------------------
    # Interne helpers
    # ------------------------------------------------------------------

    def _fmt(self, v: float) -> str:
        return f'{v:.{self._decimals}f}'

    def _to_pos(self, v: float) -> int:
        if self._hi == self._lo:
            return 0
        pos = (v - self._lo) / (self._hi - self._lo) * self._STEPS
        return max(0, min(self._STEPS, int(round(pos))))

    def _to_val(self, pos: int) -> float:
        return self._lo + (pos / self._STEPS) * (self._hi - self._lo)

    def _update_slider_pos(self) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(self._to_pos(self._val))
        self._slider.blockSignals(False)

    def _update_value_label(self) -> None:
        self._val_spin.blockSignals(True)
        self._val_spin.setValue(self._val)
        self._val_spin.blockSignals(False)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_slider_moved(self, pos: int) -> None:
        self._val = self._to_val(pos)
        self._update_value_label()
        if not self.signalsBlocked():
            self.valueChanged.emit(self._val)

    def _on_val_spin_changed(self, new_val: float) -> None:
        self._val = max(self._lo, min(self._hi, new_val))
        self._update_slider_pos()
        if not self.signalsBlocked():
            self.valueChanged.emit(self._val)

    def _on_min_changed(self, new_min: float) -> None:
        self._lo = new_min
        if self._lo >= self._hi:
            self._hi = self._lo + 0.01
            self._max_spin.blockSignals(True)
            self._max_spin.setValue(self._hi)
            self._max_spin.blockSignals(False)
        self._val_spin.setMinimum(self._lo)
        self._update_slider_pos()

    def _on_max_changed(self, new_max: float) -> None:
        self._hi = new_max
        if self._hi <= self._lo:
            self._lo = self._hi - 0.01
            self._min_spin.blockSignals(True)
            self._min_spin.setValue(self._lo)
            self._min_spin.blockSignals(False)
        self._val_spin.setMaximum(self._hi)
        self._update_slider_pos()

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_label_visible(self, visible: bool) -> None:
        """Verberg of toon de naam-rij (voor gebruik in grid-layout)."""
        self._name_row.setVisible(visible)

    def set_header_visible(self, visible: bool) -> None:
        """Toon of verberg de 'min'/'max' kolomkoppen (alleen bovenste rij)."""
        self._min_hdr.setVisible(visible)
        self._max_hdr.setVisible(visible)

    def value(self) -> float:
        return self._val

    def setValue(self, v: float) -> None:
        self._val = max(self._lo, min(self._hi, v))
        self._update_slider_pos()
        self._update_value_label()
        if not self.signalsBlocked():
            self.valueChanged.emit(self._val)

    def setEnabled(self, enabled: bool) -> None:
        """Pas ook hardcoded label-kleuren aan zodat alles consistent vergrijst."""
        super().setEnabled(enabled)
        self._name_lbl.setStyleSheet(_NAME_STYLE if enabled else _NAME_STYLE_DISABLED)
        hdr = _HDR_STYLE if enabled else _HDR_STYLE_DISABLED
        self._min_hdr.setStyleSheet(hdr)
        self._max_hdr.setStyleSheet(hdr)
