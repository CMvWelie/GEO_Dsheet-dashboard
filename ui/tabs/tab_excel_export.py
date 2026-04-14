"""Tab 4B — Excel-export."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFileDialog,
)
from PyQt6.QtCore import pyqtSignal


_BTN_PRIMARY = (
    'QPushButton { background: #245b7a; color: white; border: 1px solid #1a4560; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; } '
    'QPushButton:hover { background: #1a4560; } '
    'QPushButton:pressed { background: #122f42; }'
)
_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 4px 10px; font-size: 11px; } '
    'QPushButton:hover { background: #f0f5f9; } '
    'QPushButton:pressed { background: #e4edf3; }'
)


class TabExcelExport(QWidget):
    """Excel-exporttab (Tab 4B)."""

    export_requested = pyqtSignal(str)          # output_path
    template_changed = pyqtSignal(str)          # template_path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        tmpl_box = QGroupBox('Excel-sjabloon (optioneel)')
        tmpl_vl = QVBoxLayout(tmpl_box)
        tmpl_row = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .xltx sjabloon…')
        self._template_edit.textChanged.connect(self.template_changed)
        tmpl_browse = QPushButton('Bladeren…')
        tmpl_browse.setStyleSheet(_BTN_NORMAL)
        tmpl_browse.clicked.connect(self._browse_template)
        tmpl_row.addWidget(self._template_edit)
        tmpl_row.addWidget(tmpl_browse)
        tmpl_vl.addLayout(tmpl_row)
        root.addWidget(tmpl_box)

        out_box = QGroupBox('Uitvoerbestand')
        out_vl = QVBoxLayout(out_box)
        out_row = QHBoxLayout()
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText('Pad naar uitvoer .xlsx…')
        out_browse = QPushButton('Bladeren…')
        out_browse.setStyleSheet(_BTN_NORMAL)
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(self._output_edit)
        out_row.addWidget(out_browse)
        out_vl.addLayout(out_row)
        root.addWidget(out_box)

        self._export_btn = QPushButton('Exporteer naar Excel')
        self._export_btn.setStyleSheet(_BTN_PRIMARY)
        self._export_btn.clicked.connect(self._on_export)
        root.addWidget(self._export_btn)

        self._status_label = QLabel('')
        self._status_label.setWordWrap(True)
        root.addWidget(self._status_label)
        root.addStretch()

    def set_status(self, text: str, ok: bool = True) -> None:
        color = '#2f7d32' if ok else '#b42318'
        self._status_label.setStyleSheet(f'color:{color};font-size:11px;')
        self._status_label.setText(text)

    def get_template_path(self) -> str:
        return self._template_edit.text().strip()

    def get_output_path(self) -> str:
        return self._output_edit.text().strip()

    def _browse_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer Excel-sjabloon', '', 'Excel-sjabloon (*.xltx);;Excel (*.xlsx)')
        if path:
            self._template_edit.setText(path)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, 'Sla Excel-rapport op', 'rapport.xlsx', 'Excel (*.xlsx)')
        if path:
            self._output_edit.setText(path)

    def _on_export(self) -> None:
        path = self._output_edit.text().strip()
        if path:
            self.export_requested.emit(path)
