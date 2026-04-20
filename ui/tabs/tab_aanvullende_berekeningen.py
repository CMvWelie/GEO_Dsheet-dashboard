"""Hoofdtab Aanvullende berekeningen — container voor aanvullende geotechnische controles."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from parsers.models import Project
from ui.tabs.tab_hydraulische_grondbreuk import TabHydraulischeGrondbreuk


class TabAanvullendeBerekeningen(QWidget):
    """Container-tab met subtabs voor aanvullende geotechnische berekeningen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tab_hydraulische_grondbreuk = TabHydraulischeGrondbreuk()
        self._tabs.addTab(self._tab_hydraulische_grondbreuk, 'Hydraulische Grondbreuk')

        layout.addWidget(self._tabs)

    def update_project(self, project: Project | None) -> None:
        """Propageer projectwijziging naar alle subtabs.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        self._tab_hydraulische_grondbreuk.update_project(project)
