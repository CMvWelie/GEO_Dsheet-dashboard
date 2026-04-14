"""Tab Instellingen — persistente app-instellingen en preview-opener."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog,
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
_BTN_CLEAR = (
    'QPushButton { background: white; color: #888; border: 1px solid #ccc; '
    'border-radius: 5px; padding: 4px 6px; font-size: 11px; } '
    'QPushButton:hover { background: #fdf0ee; color: #c0392b; border-color: #c0392b; }'
)


class TabInstellingen(QWidget):
    """Tabblad met persistente applicatie-instellingen (Tab Instellingen)."""

    template_path_changed = pyqtSignal(str)
    """Afgegeven zodra het Word-template-pad wijzigt (ook bij wissen)."""

    preview_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Preview openen' klikt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Groep: Rapportage-instellingen ────────────────────────────
        tmpl_box = QGroupBox('Rapportage-instellingen')
        tmpl_vl = QVBoxLayout(tmpl_box)
        tmpl_vl.setSpacing(6)

        lbl = QLabel('Word-template (.dotx)')
        lbl.setStyleSheet('font-size: 11px; color: #444;')

        tmpl_rij = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .dotx template… (optioneel)')
        self._template_edit.textChanged.connect(self.template_path_changed)

        bladeren_btn = QPushButton('Bladeren…')
        bladeren_btn.setStyleSheet(_BTN_NORMAL)
        bladeren_btn.clicked.connect(self._on_bladeren)

        wis_btn = QPushButton('✕')
        wis_btn.setStyleSheet(_BTN_CLEAR)
        wis_btn.setFixedWidth(28)
        wis_btn.setToolTip('Verwijder template-pad')
        wis_btn.clicked.connect(self._on_wis_template)

        tmpl_rij.addWidget(self._template_edit)
        tmpl_rij.addWidget(bladeren_btn)
        tmpl_rij.addWidget(wis_btn)

        hint = QLabel(
            'Optioneel — wordt ook gebruikt bij Word-export als het export-venster leeg is'
        )
        hint.setStyleSheet('font-size: 10px; color: #888; font-style: italic;')

        tmpl_vl.addWidget(lbl)
        tmpl_vl.addLayout(tmpl_rij)
        tmpl_vl.addWidget(hint)
        root.addWidget(tmpl_box)

        # ── Groep: Preview-venster ────────────────────────────────────
        prev_box = QGroupBox('Preview-venster')
        prev_vl = QVBoxLayout(prev_box)
        prev_vl.setSpacing(6)

        prev_rij = QHBoxLayout()
        open_btn = QPushButton('↗ Preview openen')
        open_btn.setStyleSheet(_BTN_PRIMARY)
        open_btn.clicked.connect(self.preview_open_requested)

        prev_hint = QLabel('Opent een zwevend Word-preview venster naast de applicatie')
        prev_hint.setStyleSheet('font-size: 10px; color: #666;')

        prev_rij.addWidget(open_btn)
        prev_rij.addWidget(prev_hint)
        prev_rij.addStretch()
        prev_vl.addLayout(prev_rij)
        root.addWidget(prev_box)

        root.addStretch()

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_template_path(self, pad: str) -> None:
        """Toon een opgeslagen template-pad zonder een signal af te geven.

        Parameters
        ----------
        pad:
            Te tonen bestandspad (leeg = veld wissen).
        """
        self._template_edit.blockSignals(True)
        self._template_edit.setText(pad)
        self._template_edit.blockSignals(False)

    # ------------------------------------------------------------------
    # Privé handlers
    # ------------------------------------------------------------------

    def _on_bladeren(self) -> None:
        pad, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer Word-template', '', 'Word-sjabloon (*.dotx);;Word (*.docx)'
        )
        if pad:
            self._template_edit.setText(pad)

    def _on_wis_template(self) -> None:
        self._template_edit.clear()
