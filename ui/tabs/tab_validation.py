"""Tab 5 — Validatie: controle van het rapportpakket voor export."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from reporting.validation import ValidationIssue


_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; } '
    'QPushButton:hover { background: #f0f5f9; } '
    'QPushButton:pressed { background: #e4edf3; }'
)

_SEVERITY_COLORS = {
    'error':   QColor('#fde0dc'),
    'warning': QColor('#fff7eb'),
}


class TabValidation(QWidget):
    """Validatietab (Tab 5): toont ValidationIssues na het controleren van het rapport."""

    validate_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        self._validate_btn = QPushButton('Valideer rapport')
        self._validate_btn.setStyleSheet(_BTN_NORMAL)
        self._validate_btn.clicked.connect(self.validate_requested)
        root.addWidget(self._validate_btn)

        self._summary_label = QLabel('')
        self._summary_label.setWordWrap(True)
        root.addWidget(self._summary_label)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(['Ernst', 'Veld', 'Melding'])
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        root.addWidget(self._table, stretch=1)

    def populate(self, issues: list[ValidationIssue]) -> None:
        """Vul de tabel met validatieproblemen."""
        self._table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            for col, text in enumerate([issue.severity.upper(), issue.field, issue.message]):
                item = QTableWidgetItem(text)
                bg = _SEVERITY_COLORS.get(issue.severity)
                if bg:
                    item.setBackground(bg)
                self._table.setItem(row, col, item)

        errors = sum(1 for i in issues if i.severity == 'error')
        warnings = sum(1 for i in issues if i.severity == 'warning')
        if not issues:
            self._summary_label.setStyleSheet('color:#2f7d32;font-weight:bold;')
            self._summary_label.setText('Geen problemen gevonden. Rapport is gereed voor export.')
        else:
            self._summary_label.setStyleSheet('color:#b42318;font-weight:bold;')
            self._summary_label.setText(
                f'{errors} fout(en), {warnings} waarschuwing(en) gevonden.')
