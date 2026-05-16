"""Tab 4A — Rapportageselectie: items selecteren, ordenen, exportdoel instellen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QLineEdit, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal

from reporting.models import ReportItem
from reporting.selection import ReportPlan


class TabReportSelect(QWidget):
    """Rapportage-item selectietab (Tab 4A)."""

    selection_changed = pyqtSignal()
    word_pdf_preview_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Word preview (WYSIWYG)' klikt."""
    word_preview_win32_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Word preview (Word-vensters behouden)' klikt."""
    export_word_requested = pyqtSignal(str)
    template_path_changed = pyqtSignal(str)

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
            b.setObjectName('btnNormal')
            btn_row.addWidget(b)
        btn_row.addStretch()
        vl.addLayout(btn_row)

        root.addWidget(box, stretch=1)

        word_box = QGroupBox('Word-rapportage')
        word_vl = QVBoxLayout(word_box)

        tmpl_lbl = QLabel('Word-template (.dotx)')
        tmpl_lbl.setObjectName('hintLabel')
        word_vl.addWidget(tmpl_lbl)

        tmpl_row = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .dotx template... (optioneel)')
        self._template_edit.textChanged.connect(self.template_path_changed)
        tmpl_browse = QPushButton('Bladeren...')
        tmpl_browse.setObjectName('btnNormal')
        tmpl_browse.clicked.connect(self._browse_template)
        tmpl_clear = QPushButton('X')
        tmpl_clear.setObjectName('btnClear')
        tmpl_clear.setFixedWidth(28)
        tmpl_clear.setToolTip('Verwijder template-pad')
        tmpl_clear.clicked.connect(self._template_edit.clear)
        tmpl_row.addWidget(self._template_edit)
        tmpl_row.addWidget(tmpl_browse)
        tmpl_row.addWidget(tmpl_clear)
        word_vl.addLayout(tmpl_row)

        export_row = QHBoxLayout()
        export_btn = QPushButton('Exporteer naar Word')
        export_btn.setObjectName('btnPrimary')
        export_btn.clicked.connect(self._on_export_word)
        export_row.addWidget(export_btn)
        export_row.addStretch()
        word_vl.addLayout(export_row)

        self._word_status = QLabel('')
        self._word_status.setWordWrap(True)
        word_vl.addWidget(self._word_status)

        root.addWidget(word_box)

        # ── Preview-vensters ──────────────────────────────────────────
        wysiwyg_rij = QHBoxLayout()
        self._word_preview_btn = QPushButton('📄 Word preview (WYSIWYG)')
        self._word_preview_btn.setObjectName('btnPrimary')
        self._word_preview_btn.clicked.connect(
            self.word_pdf_preview_open_requested
        )
        self._word_preview_win32_btn = QPushButton('📄 Word preview (Word open)')
        self._word_preview_win32_btn.setObjectName('btnNormal')
        self._word_preview_win32_btn.setToolTip(
            'Zelfde preview, maar sluit geen open Word-vensters'
        )
        self._word_preview_win32_btn.clicked.connect(
            self.word_preview_win32_open_requested
        )
        wysiwyg_hint = QLabel(
            'Genereert het echte .docx en toont als PDF — exact zoals in Word'
        )
        wysiwyg_hint.setObjectName('hintLabel')
        wysiwyg_rij.addWidget(self._word_preview_btn)
        wysiwyg_rij.addWidget(self._word_preview_win32_btn)
        wysiwyg_rij.addWidget(wysiwyg_hint)
        wysiwyg_rij.addStretch()
        root.addLayout(wysiwyg_rij)

        self._up_btn.clicked.connect(self._move_up)
        self._down_btn.clicked.connect(self._move_down)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def set_plan(self, plan: ReportPlan) -> None:
        self._plan = plan
        self._refresh()

    def set_template_path(self, pad: str) -> None:
        self._template_edit.blockSignals(True)
        self._template_edit.setText(pad)
        self._template_edit.blockSignals(False)

    def set_word_status(self, text: str, ok: bool = True) -> None:
        color = '#2f7d32' if ok else '#b42318'
        self._word_status.setStyleSheet(f'color:{color};font-size:11px;')
        self._word_status.setText(text)

    def set_word_pdf_preview_enabled(self, beschikbaar: bool,
                                       tooltip: str = '') -> None:
        """Schakel de WYSIWYG-knop in/uit op basis van engine-beschikbaarheid.

        Parameters
        ----------
        beschikbaar:
            True als minstens één conversie-engine beschikbaar is.
        tooltip:
            Hint die bij hover getoond wordt (bijv. installatie-instructie).
        """
        self._word_preview_btn.setEnabled(beschikbaar)
        self._word_preview_btn.setToolTip(tooltip)

    def set_word_preview_win32_enabled(self, beschikbaar: bool) -> None:
        """Schakel de win32-preview-knop in/uit op basis van win32com-beschikbaarheid.

        Parameters
        ----------
        beschikbaar:
            True als pywin32 beschikbaar is.
        """
        self._word_preview_win32_btn.setEnabled(beschikbaar)
        if not beschikbaar:
            self._word_preview_win32_btn.setToolTip('pywin32 niet beschikbaar')

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

    def _browse_template(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, 'Selecteer Word-template', '', 'Word-sjabloon (*.dotx);;Word (*.docx)'
        )
        if path:
            self._template_edit.setText(path)

    def _on_export_word(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, 'Sla Word-rapport op', 'rapport.docx', 'Word (*.docx)'
        )
        if path:
            self.export_word_requested.emit(path)
