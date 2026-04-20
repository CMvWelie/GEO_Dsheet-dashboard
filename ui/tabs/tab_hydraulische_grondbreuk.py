"""Subtab Hydraulische Grondbreuk — controle conform NEN 9997-1:2016."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from parsers.models import Project
from utils.formatting import fmt_number

_MATERIAALFACTOR_STANDAARD = 0.9
_WATERGEWICHT_STANDAARD = 10.0


@dataclass
class AutoWaarden:
    """Waarden die automatisch uit een Project worden ingevuld."""
    inheiniveau: float | None
    grondwaterstand: float | None
    grondgewicht: float | None


def extraheer_auto_waarden(project: Project) -> AutoWaarden:
    """Leid auto-invulwaarden af uit een Project.

    Parameters
    ----------
    project:
        Geparseerd D-Sheet project.

    Returns
    -------
    AutoWaarden
        Inheiniveau, grondwaterstand en grondgewicht, of None als niet beschikbaar.
    """
    inheiniveau = project.sheet_piling[0].bottom if project.sheet_piling else None
    grondwaterstand = (
        max(wl.level for wl in project.waterlevels)
        if project.waterlevels else None
    )
    grondgewicht = project.soils[0].gamma_wet if project.soils else None
    return AutoWaarden(
        inheiniveau=inheiniveau,
        grondwaterstand=grondwaterstand,
        grondgewicht=grondgewicht,
    )


def bereken_hydraulische_grondbreuk(
    bouwputniveau: float,
    inheiniveau: float,
    grondgewicht: float,
    grondwaterstand: float,
    materiaalfactor: float,
    watergewicht: float,
) -> tuple[float, float, float]:
    """Bereken de hydraulische grondbreukcontrole conform NEN 9997-1:2016.

    Parameters
    ----------
    bouwputniveau:   Ontgravingsniveau bouwput [m NAP].
    inheiniveau:     Onderkant damwand [m NAP].
    grondgewicht:    Volumegewicht grond gamma [kN/m3].
    grondwaterstand: Grondwaterstand buiten bouwput [m NAP].
    materiaalfactor: Materiaalfactor psi [-].
    watergewicht:    Volumegewicht water gamma_w [kN/m3].

    Returns
    -------
    tuple[float, float, float]
        (P_stab [kN/m2], P_water [kN/m2], UC [-]).
        UC is inf als P_water nul is.
    """
    dikte_grondwig = bouwputniveau - inheiniveau
    p_stab = dikte_grondwig * grondgewicht * materiaalfactor
    p_water = (grondwaterstand - inheiniveau) * watergewicht
    uc = p_stab / p_water if p_water != 0.0 else math.inf
    return p_stab, p_water, uc


class TabHydraulischeGrondbreuk(QWidget):
    """Subtab met hydraulische grondbreukcontrole (NEN 9997-1:2016)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._auto_waarden: AutoWaarden | None = None
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._bouw_invoergroep())
        layout.addWidget(self._bouw_resultaatgroep())
        layout.addStretch()
        self._verbind_signalen()
        self._herbereken()

    def _bouw_invoergroep(self) -> QGroupBox:
        groep = QGroupBox('Invoer')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._spin_bouwput = self._maak_spin(-50.0, 50.0, 2)
        self._spin_inhei = self._maak_spin(-50.0, 50.0, 2)
        self._spin_grondgewicht = self._maak_spin(0.0, 40.0, 1)
        self._spin_grondwater = self._maak_spin(-50.0, 50.0, 2)
        self._spin_materiaalfactor = self._maak_spin(0.0, 2.0, 2)
        self._spin_watergewicht = self._maak_spin(0.0, 20.0, 1)

        self._spin_materiaalfactor.setValue(_MATERIAALFACTOR_STANDAARD)
        self._spin_watergewicht.setValue(_WATERGEWICHT_STANDAARD)

        self._btn_reset_inhei = self._maak_reset_knop()
        self._btn_reset_grondwater = self._maak_reset_knop()
        self._btn_reset_grondgewicht = self._maak_reset_knop()

        rijen: list[tuple[str, QDoubleSpinBox, QPushButton | None]] = [
            ('Bouwputniveau (m NAP)', self._spin_bouwput, None),
            ('Inheiniveau damwand (m NAP)', self._spin_inhei, self._btn_reset_inhei),
            ('Grondgewicht gamma (kN/m3)', self._spin_grondgewicht, self._btn_reset_grondgewicht),
            ('Grondwaterstand buiten (m NAP)', self._spin_grondwater, self._btn_reset_grondwater),
            ('Materiaalfactor psi (-)', self._spin_materiaalfactor, None),
            ('Watergewicht gamma_w (kN/m3)', self._spin_watergewicht, None),
        ]
        for rij, (label_tekst, spin, reset) in enumerate(rijen):
            grid.addWidget(QLabel(label_tekst), rij, 0)
            grid.addWidget(spin, rij, 1)
            if reset is not None:
                grid.addWidget(reset, rij, 2)

        return groep

    def _bouw_resultaatgroep(self) -> QGroupBox:
        groep = QGroupBox('Resultaat')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._lbl_p_stab = QLabel('-')
        self._lbl_p_water = QLabel('-')
        self._lbl_uc = QLabel('-')

        font_groot = QFont()
        font_groot.setPointSize(14)
        font_groot.setBold(True)
        self._lbl_uc.setFont(font_groot)

        self._lbl_status = QLabel('-')
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setMinimumHeight(44)

        grid.addWidget(QLabel('Stabiliserende druk'), 0, 0)
        grid.addWidget(self._lbl_p_stab, 0, 1)
        grid.addWidget(QLabel('Aandrijvende waterdruk'), 1, 0)
        grid.addWidget(self._lbl_p_water, 1, 1)
        grid.addWidget(QLabel('Gebruiksgraad (UC)'), 2, 0)
        grid.addWidget(self._lbl_uc, 2, 1)
        grid.addWidget(self._lbl_status, 3, 0, 1, 2)

        return groep

    def _maak_spin(self, minimum: float, maximum: float, decimalen: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimalen)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(110)
        return spin

    def _maak_reset_knop(self) -> QPushButton:
        btn = QPushButton('↺')
        btn.setFixedWidth(30)
        btn.setToolTip('Terugzetten naar projectwaarde')
        return btn

    def _verbind_signalen(self) -> None:
        for spin in [
            self._spin_bouwput, self._spin_inhei, self._spin_grondgewicht,
            self._spin_grondwater, self._spin_materiaalfactor, self._spin_watergewicht,
        ]:
            spin.valueChanged.connect(self._herbereken)
        self._btn_reset_inhei.clicked.connect(self._reset_inhei)
        self._btn_reset_grondwater.clicked.connect(self._reset_grondwater)
        self._btn_reset_grondgewicht.clicked.connect(self._reset_grondgewicht)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------
    def update_project(self, project: Project | None) -> None:
        """Vul invoervelden automatisch in vanuit project.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        if project is None:
            self._auto_waarden = None
            return
        self._auto_waarden = extraheer_auto_waarden(project)
        self._reset_inhei()
        self._reset_grondwater()
        self._reset_grondgewicht()

    # ------------------------------------------------------------------
    # Reset-handlers
    # ------------------------------------------------------------------
    def _reset_inhei(self) -> None:
        if self._auto_waarden and self._auto_waarden.inheiniveau is not None:
            self._spin_inhei.blockSignals(True)
            self._spin_inhei.setValue(self._auto_waarden.inheiniveau)
            self._spin_inhei.blockSignals(False)
        self._herbereken()

    def _reset_grondwater(self) -> None:
        if self._auto_waarden and self._auto_waarden.grondwaterstand is not None:
            self._spin_grondwater.blockSignals(True)
            self._spin_grondwater.setValue(self._auto_waarden.grondwaterstand)
            self._spin_grondwater.blockSignals(False)
        self._herbereken()

    def _reset_grondgewicht(self) -> None:
        if self._auto_waarden and self._auto_waarden.grondgewicht is not None:
            self._spin_grondgewicht.blockSignals(True)
            self._spin_grondgewicht.setValue(self._auto_waarden.grondgewicht)
            self._spin_grondgewicht.blockSignals(False)
        self._herbereken()

    # ------------------------------------------------------------------
    # Berekening
    # ------------------------------------------------------------------
    def _herbereken(self) -> None:
        p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
            bouwputniveau=self._spin_bouwput.value(),
            inheiniveau=self._spin_inhei.value(),
            grondgewicht=self._spin_grondgewicht.value(),
            grondwaterstand=self._spin_grondwater.value(),
            materiaalfactor=self._spin_materiaalfactor.value(),
            watergewicht=self._spin_watergewicht.value(),
        )
        self._lbl_p_stab.setText(f'{fmt_number(p_stab, 2)} kN/m²')
        self._lbl_p_water.setText(f'{fmt_number(p_water, 2)} kN/m²')
        uc_tekst = fmt_number(uc, 3) if not math.isinf(uc) else '∞'
        self._lbl_uc.setText(uc_tekst)

        voldoet = uc >= 1.0
        status_tekst = 'VOLDOET' if voldoet else 'VOLDOET NIET'
        kleur = '#2e7d32' if voldoet else '#c62828'
        self._lbl_status.setText(status_tekst)
        self._lbl_status.setStyleSheet(
            f'background-color: {kleur}; color: white; font-weight: bold;'
            f' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )
