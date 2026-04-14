"""Tab 4A — Rapportageselectie: items selecteren, ordenen, exportdoel instellen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from reporting.models import ReportItem
from reporting.selection import ReportPlan


_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 4px 10px; font-size: 11px; } '
    'QPushButton:hover { background: #f0f5f9; } '
    'QPushButton:pressed { background: #e4edf3; }'
)


class TabReportSelect(QWidget):
    """Rapportage-item selectietab (Tab 4A)."""

    selection_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plan: ReportPlan | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        root.addWidget(QLabel(
            'Selecteer de rapportage-items die worden opgenomen in de export. '
            'Gebruik de knoppen om de volgorde aan te passen.'
        ))

        box = QGroupBox('Geselecteerde items')
        vl = QVBoxLayout(box)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        vl.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._up_btn = QPushButton('↑ Omhoog')
        self._down_btn = QPushButton('↓ Omlaag')
        self._remove_btn = QPushButton('Verwijder')
        for b in [self._up_btn, self._down_btn, self._remove_btn]:
            b.setStyleSheet(_BTN_NORMAL)
            btn_row.addWidget(b)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        root.addWidget(box, stretch=1)

        self._up_btn.clicked.connect(self._move_up)
        self._down_btn.clicked.connect(self._move_down)
        self._remove_btn.clicked.connect(self._remove_selected)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def set_plan(self, plan: ReportPlan) -> None:
        self._plan = plan
        self._refresh()

    def _refresh(self) -> None:
        self._list.clear()
        if not self._plan:
            return
        for item in self._plan.items:
            lw = QListWidgetItem(f'[{item.kind}] {item.caption}')
            lw.setData(Qt.ItemDataRole.UserRole, item.id)
            self._list.addItem(lw)

    def _move_up(self) -> None:
        row = self._list.currentRow()
        if self._plan and row > 0:
            item = self._plan.items[row]
            self._plan.reorder(item.id, row - 1)
            self._refresh()
            self._list.setCurrentRow(row - 1)
            self.selection_changed.emit()

    def _move_down(self) -> None:
        row = self._list.currentRow()
        if self._plan and 0 <= row < len(self._plan.items) - 1:
            item = self._plan.items[row]
            self._plan.reorder(item.id, row + 1)
            self._refresh()
            self._list.setCurrentRow(row + 1)
            self.selection_changed.emit()

    def _remove_selected(self) -> None:
        row = self._list.currentRow()
        if self._plan and row >= 0:
            item_id = self._list.item(row).data(Qt.ItemDataRole.UserRole)
            self._plan.remove_item(item_id)
            self._refresh()
            self.selection_changed.emit()
