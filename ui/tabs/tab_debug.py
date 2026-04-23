"""Hoofdtab Debug — container met subtabs Invoer en Uitvoer."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from parsers.models import Project
from ui.tabs.tab_debug_invoer import TabDebugInvoer
from ui.tabs.tab_debug_uitvoer import TabDebugUitvoer


class TabDebug(QWidget):
    """Container-tab met subtabs voor het inspecteren van alle geparste projectdata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tab_invoer = TabDebugInvoer()
        self._tab_uitvoer = TabDebugUitvoer()
        self._tabs.addTab(self._tab_invoer, 'Invoer')
        self._tabs.addTab(self._tab_uitvoer, 'Uitvoer')

        layout.addWidget(self._tabs)

    def update_project(self, project: Project | None) -> None:
        """Propageer projectwijziging naar beide subtabs.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        self._tab_invoer.update_project(project)
        self._tab_uitvoer.update_project(project)
