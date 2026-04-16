"""Tab 4A — Rapportageselectie: items selecteren, ordenen, exportdoel instellen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox,
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
_BTN_PRIMARY = (
    'QPushButton { background: #245b7a; color: white; border: 1px solid #1a4560; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; } '
    'QPushButton:hover { background: #1a4560; } '
    'QPushButton:pressed { background: #122f42; }'
)


class TabReportSelect(QWidget):
    """Rapportage-item selectietab (Tab 4A)."""

    selection_changed = pyqtSignal()
    preview_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Preview openen' klikt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plan: ReportPlan | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        root.addWidget(QLabel(
            'Vink items aan of uit om ze op te nemen in de export. '
            'Gebruik de knoppen om de volgorde aan te passen.'
        ))

        box = QGroupBox('Rapportage-items')
        vl = QVBoxLayout(box)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.itemChanged.connect(self._on_item_changed)
        vl.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._up_btn = QPushButton('↑ Omhoog')
        self._down_btn = QPushButton('↓ Omlaag')
        for b in [self._up_btn, self._down_btn]:
            b.setStyleSheet(_BTN_NORMAL)
            btn_row.addWidget(b)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        root.addWidget(box, stretch=1)

        # ── Preview-venster ────────────────────────────────────────────
        prev_rij = QHBoxLayout()
        open_btn = QPushButton('↗ Preview openen')
        open_btn.setStyleSheet(_BTN_PRIMARY)
        open_btn.clicked.connect(self.preview_open_requested)
        prev_hint = QLabel('Opent een zwevend Word-preview venster naast de applicatie')
        prev_hint.setStyleSheet('font-size: 10px; color: #666;')
        prev_rij.addWidget(open_btn)
        prev_rij.addWidget(prev_hint)
        prev_rij.addStretch()
        root.addLayout(prev_rij)

        self._up_btn.clicked.connect(self._move_up)
        self._down_btn.clicked.connect(self._move_down)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def set_plan(self, plan: ReportPlan) -> None:
        self._plan = plan
        self._refresh()

    def _refresh(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        if self._plan:
            for item in self._plan.items:
                lw = QListWidgetItem(f'[{item.kind}] {item.caption}')
                lw.setData(Qt.ItemDataRole.UserRole, item.id)
                lw.setFlags(lw.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                actief = item.included_excel or item.included_word
                lw.setCheckState(
                    Qt.CheckState.Checked if actief else Qt.CheckState.Unchecked
                )
                self._list.addItem(lw)
        self._list.blockSignals(False)

    # ------------------------------------------------------------------
    # Privé handlers
    # ------------------------------------------------------------------

    def _on_item_changed(self, lw: QListWidgetItem) -> None:
        """Verwerk vinkje-wijziging: sla nieuw exportdoel op in het plan."""
        if not self._plan:
            return
        item_id = lw.data(Qt.ItemDataRole.UserRole)
        actief = lw.checkState() == Qt.CheckState.Checked
        self._plan.set_destination(item_id, excel=actief, word=actief)
        self.selection_changed.emit()

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

