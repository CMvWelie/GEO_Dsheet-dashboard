"""Tab 0 — Rapportcontext: projectmetadata voor rapportage."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QGroupBox, QLabel,
    QHBoxLayout, QPushButton, QFileDialog, QSizePolicy,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, Qt

from reporting.models import ReportMetadata


_LOGO_DISPLAY_HEIGHT = 80  # px


class TabReportContext(QWidget):
    """Formulier voor het invullen van rapportmetadata (Tab 0)."""

    metadata_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logo_path: str = ''
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # --- Metadatavelden ---
        box = QGroupBox('Rapportgegevens')
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._fields: dict[str, QLineEdit] = {}
        for attr, label in [
            ('client',       'Opdrachtgever'),
            ('project_name', 'Project'),
            ('onderdeel',    'Onderdeel'),
            ('author',       'Auteur'),
            ('date',         'Datum'),
            ('revision',     'Versie'),
        ]:
            edit = QLineEdit()
            edit.textChanged.connect(self.metadata_changed)
            self._fields[attr] = edit
            form.addRow(QLabel(label), edit)

        root.addWidget(box)

        # --- Logo ---
        logo_box = QGroupBox('Logo')
        logo_layout = QVBoxLayout(logo_box)
        logo_layout.setSpacing(8)

        self._logo_label = QLabel('Geen logo geselecteerd')
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(_LOGO_DISPLAY_HEIGHT)
        self._logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._logo_label.setStyleSheet(
            'border: 1px solid #aaa; background: #f5f5f5; color: #888;'
        )
        logo_layout.addWidget(self._logo_label)

        btn_row = QHBoxLayout()
        self._btn_browse = QPushButton('Bladeren…')
        self._btn_browse.clicked.connect(self._browse_logo)
        self._btn_clear = QPushButton('Wissen')
        self._btn_clear.clicked.connect(self._clear_logo)
        btn_row.addWidget(self._btn_browse)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        logo_layout.addLayout(btn_row)

        root.addWidget(logo_box)
        root.addStretch()

    # ------------------------------------------------------------------
    # Logo-acties
    # ------------------------------------------------------------------

    def _browse_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Logo selecteren',
            '',
            'Afbeeldingen (*.png *.jpg *.jpeg)',
        )
        if path:
            self._set_logo(path)

    def _clear_logo(self) -> None:
        self._set_logo('')

    def _set_logo(self, path: str) -> None:
        self._logo_path = path
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaledToHeight(
                    _LOGO_DISPLAY_HEIGHT,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._logo_label.setPixmap(pix)
                self._logo_label.setText('')
            else:
                self._logo_label.setPixmap(QPixmap())
                self._logo_label.setText('Kan afbeelding niet laden')
        else:
            self._logo_label.setPixmap(QPixmap())
            self._logo_label.setText('Geen logo geselecteerd')
        self.metadata_changed.emit()

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def get_metadata(self) -> ReportMetadata:
        """Lees de huidige invoerveldwaarden als ReportMetadata."""
        md = ReportMetadata(**{k: v.text() for k, v in self._fields.items()})
        md.logo_path = self._logo_path
        return md

    def set_metadata(self, md: ReportMetadata) -> None:
        """Vul formuliervelden in vanuit een ReportMetadata object."""
        for attr, edit in self._fields.items():
            edit.blockSignals(True)
            edit.setText(getattr(md, attr, '') or '')
            edit.blockSignals(False)
        self._set_logo(md.logo_path or '')
