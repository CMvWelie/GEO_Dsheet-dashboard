"""Tab 1 — Import: bestandsingest en projectselectie."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QGroupBox, QAbstractItemView, QSizePolicy,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.status_widget import StatusWidget


_BTN_PRIMARY = (
    'QPushButton { background: #245b7a; color: white; border: 1px solid #1a4560; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; } '
    'QPushButton:hover { background: #1a4560; } '
    'QPushButton:pressed { background: #122f42; border-top: 2px solid #0d2233; }'
)
_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 500; } '
    'QPushButton:hover { background: #f0f5f9; border-color: #7a9eb0; } '
    'QPushButton:pressed { background: #e4edf3; }'
)
_BTN_DANGER = (
    'QPushButton { background: white; color: #c0392b; border: 1px solid #e08070; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 500; } '
    'QPushButton:hover { background: #fdf0ee; border-color: #c0392b; } '
    'QPushButton:pressed { background: #fde0dc; }'
)


class TabImport(QWidget):
    """Bestandsimport tab (Tab 1).

    Signalen:
        project_selected(base_name)  — gebruiker klikt op een project in de lijst
        remove_requested(base_name)  — gebruiker klikt op "Verwijder project"
    """

    project_selected = pyqtSignal(str)
    remove_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)

        # ── Linkerpaneel ────────────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 6, 12)
        left_layout.setSpacing(8)

        drop_label = QLabel('Sleep bestanden hierheen\nof gebruik de knop hieronder:')
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet(
            'border: 2px dashed #8ea4b5; border-radius: 8px;'
            'background: #fafcfd; padding: 20px; color: #5f6b76; font-size: 11px;'
        )
        drop_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(drop_label, stretch=1)

        self.import_btn = QPushButton('Importeer…')
        self.import_btn.setStyleSheet(_BTN_PRIMARY)
        self.import_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(self.import_btn)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.setStyleSheet(_BTN_DANGER)
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(self.reset_btn)

        self.remove_btn = QPushButton('Verwijder project')
        self.remove_btn.setStyleSheet(_BTN_DANGER)
        self.remove_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        left_layout.addWidget(self.remove_btn)

        status_box = QGroupBox('Status')
        svl = QVBoxLayout(status_box)
        self.status_widget = StatusWidget()
        svl.addWidget(self.status_widget)
        left_layout.addWidget(status_box)

        # ── Rechterpaneel ───────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 12, 12, 12)

        projects_box = QGroupBox('Ingeladen projecten')
        pvl = QVBoxLayout(projects_box)
        self.files_list = QListWidget()
        self.files_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.files_list.setAlternatingRowColors(True)
        self.files_list.setStyleSheet('font-size: 12px;')
        self.files_list.currentItemChanged.connect(self._on_selection_changed)
        self.files_list.itemClicked.connect(self._on_item_clicked)
        pvl.addWidget(self.files_list)
        right_layout.addWidget(projects_box)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Interne handlers
    # ------------------------------------------------------------------

    def _on_selection_changed(self, current: QListWidgetItem | None, _prev) -> None:
        self.remove_btn.setEnabled(current is not None)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        base_name = item.data(Qt.ItemDataRole.UserRole)
        if base_name:
            self.project_selected.emit(base_name)

    def _on_remove_clicked(self) -> None:
        item = self.files_list.currentItem()
        if item:
            base_name = item.data(Qt.ItemDataRole.UserRole)
            if base_name:
                self.remove_requested.emit(base_name)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def refresh_projects(self, projects: dict) -> None:
        """Vul de lijst met projectnamen (één rij per project)."""
        current_key = None
        current_item = self.files_list.currentItem()
        if current_item:
            current_key = current_item.data(Qt.ItemDataRole.UserRole)

        self.files_list.blockSignals(True)
        self.files_list.clear()
        for base_name, proj in projects.items():
            label = getattr(proj, 'project_name', None) or base_name
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, base_name)
            self.files_list.addItem(item)

        # Herstel selectie indien mogelijk
        if current_key:
            self.select_project(current_key)
        self.files_list.blockSignals(False)
        self.remove_btn.setEnabled(self.files_list.currentItem() is not None)

    def select_project(self, base_name: str) -> None:
        """Selecteer een project in de lijst op basis van base_name."""
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == base_name:
                self.files_list.blockSignals(True)
                self.files_list.setCurrentItem(item)
                self.files_list.blockSignals(False)
                self.remove_btn.setEnabled(True)
                return
