"""Widget voor de lijst van geïmporteerde bestanden."""

from __future__ import annotations
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt


class FileListWidget(QListWidget):
    """QListWidget die geïmporteerde D-Sheet bestanden toont."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setAlternatingRowColors(True)
        self.setMaximumHeight(200)

    def set_files(self, files: dict[str, str]) -> None:
        """Vul de lijst met bestandsnamen.

        Parameters
        ----------
        files: Dict filename → raw text.
        """
        self.clear()
        for name in sorted(files.keys()):
            item = QListWidgetItem(name)
            item.setToolTip(f'{len(files[name]):,} tekens')
            self.addItem(item)
