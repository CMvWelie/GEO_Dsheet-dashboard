"""BestandMenuButton — 'Bestand'-knop met uitklapmenu (vervangt logo-corner)."""

from __future__ import annotations

from PyQt6.QtWidgets import QToolButton, QMenu
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

    def __init__(self, parent: QToolButton | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
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

        self.setMenu(menu)
