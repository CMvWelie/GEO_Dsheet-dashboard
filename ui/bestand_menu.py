"""BestandMenuButton — 'Bestand'-knop met uitklapmenu (vervangt logo-corner)."""

from __future__ import annotations

from PyQt6.QtWidgets import QToolButton, QMenu, QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction


class BestandMenuButton(QToolButton):
    """Knop die een 'Bestand'-menu toont, vergelijkbaar met het Bestand-tabblad in Word.

    Signals
    -------
    nieuw_gevraagd:
        Gebruiker kiest 'Nieuw'.
    openen_gevraagd:
        Gebruiker kiest 'Openen…'.
    opslaan_gevraagd:
        Gebruiker kiest 'Opslaan'.
    opslaan_als_gevraagd:
        Gebruiker kiest 'Opslaan als…'.
    info_gevraagd:
        Gebruiker kiest 'Informatie / Help'.
    """

    nieuw_gevraagd = pyqtSignal()
    openen_gevraagd = pyqtSignal()
    opslaan_gevraagd = pyqtSignal()
    opslaan_als_gevraagd = pyqtSignal()
    info_gevraagd = pyqtSignal()
    herstart_gevraagd = pyqtSignal()
    instellingen_gevraagd = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        """Bouw menu-items aan en verbind signals."""
        self.setText('Bestand')
        self.setObjectName('bestandMenuBtn')
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        menu = QMenu(self)

        act_nieuw = QAction('Nieuw', self)
        act_nieuw.setShortcut('Ctrl+N')
        act_nieuw.triggered.connect(self.nieuw_gevraagd)
        menu.addAction(act_nieuw)

        act_openen = QAction('Openen…', self)
        act_openen.setShortcut('Ctrl+O')
        act_openen.triggered.connect(self.openen_gevraagd)
        menu.addAction(act_openen)

        menu.addSeparator()

        act_opslaan = QAction('Opslaan', self)
        act_opslaan.setShortcut('Ctrl+S')
        act_opslaan.triggered.connect(self.opslaan_gevraagd)
        menu.addAction(act_opslaan)

        act_opslaan_als = QAction('Opslaan als…', self)
        act_opslaan_als.setShortcut('Ctrl+Shift+S')
        act_opslaan_als.triggered.connect(self.opslaan_als_gevraagd)
        menu.addAction(act_opslaan_als)

        menu.addSeparator()

        act_info = QAction('Informatie / Help', self)
        act_info.triggered.connect(self.info_gevraagd)
        menu.addAction(act_info)

        menu.addSeparator()

        act_herstart = QAction('Applicatie herstarten', self)
        act_herstart.triggered.connect(self.herstart_gevraagd)
        menu.addAction(act_herstart)

        act_instellingen = QAction('Instellingen', self)
        act_instellingen.triggered.connect(self.instellingen_gevraagd)
        menu.addAction(act_instellingen)

        self.setMenu(menu)
