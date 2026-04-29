"""Tab 0 — Rapportcontext: projectmetadata en bestandsimport gecombineerd."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QGroupBox, QLabel,
    QHBoxLayout, QPushButton, QFileDialog, QSizePolicy, QListWidget,
    QListWidgetItem, QAbstractItemView, QSplitter, QFrame,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, Qt

from reporting.models import ReportMetadata
from ui.status_widget import StatusWidget


_LOGO_DISPLAY_HEIGHT = 80  # px


class TabReportContext(QWidget):
    """Gecombineerde tab voor rapportmetadata en bestandsimport (Tab 0)."""

    metadata_changed = pyqtSignal()
    project_selected = pyqtSignal(str)
    remove_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logo_path: str = ''
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # --- Bovenste rij: Rapportgegevens (75%) + Logo (25%) naast elkaar ---
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Rapportgegevens
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

        top_row.addWidget(box, stretch=3)

        # Logo
        logo_box = QGroupBox('Logo')
        logo_layout = QVBoxLayout(logo_box)
        logo_layout.setSpacing(8)

        self._logo_label = QLabel('Geen logo geselecteerd')
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setMinimumHeight(_LOGO_DISPLAY_HEIGHT)
        self._logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._logo_label.setStyleSheet(
            'border: 1px solid #aaa; background: #f5f5f5; color: #888;'
        )
        logo_layout.addWidget(self._logo_label, stretch=1)

        btn_row = QHBoxLayout()
        self._btn_browse = QPushButton('Bladeren…')
        self._btn_browse.setObjectName('btnNormal')
        self._btn_browse.clicked.connect(self._browse_logo)
        self._btn_clear = QPushButton('Wissen')
        self._btn_clear.setObjectName('btnNormal')
        self._btn_clear.clicked.connect(self._clear_logo)
        btn_row.addWidget(self._btn_browse)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        logo_layout.addLayout(btn_row)

        top_row.addWidget(logo_box, stretch=1)
        root.addLayout(top_row)

        # --- Horizontale scheidingslijn ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(separator)

        # --- Import knoppen ---
        import_layout = QVBoxLayout()
        import_layout.setSpacing(6)

        self.import_btn = QPushButton('Importeer…')
        self.import_btn.setObjectName('btnPrimary')
        self.import_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.import_btn)

        self.reset_btn = QPushButton('Reset')
        self.reset_btn.setObjectName('btnDanger')
        self.reset_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        import_layout.addWidget(self.reset_btn)

        self.remove_btn = QPushButton('Verwijder project')
        self.remove_btn.setObjectName('btnDanger')
        self.remove_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        import_layout.addWidget(self.remove_btn)

        # --- Splitter: drop-zone + knoppen + status | ingeladen projecten ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)

        # Linkerpaneel: drop-zone + importknoppen + status
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(8)

        drop_label = QLabel('Sleep bestanden hierheen\nof gebruik de knop hieronder.')
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet(
            'border: 2px dashed #8ea4b5; border-radius: 8px;'
            'background: #fafcfd; padding: 20px; color: #5f6b76; font-size: 11px;'
        )
        drop_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(drop_label, stretch=1)

        left_layout.addLayout(import_layout)

        status_box = QGroupBox('Status')
        svl = QVBoxLayout(status_box)
        self.status_widget = StatusWidget()
        svl.addWidget(self.status_widget)
        left_layout.addWidget(status_box)

        # Rechterpaneel: projectenlijst
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 0, 0, 0)

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

        root.addWidget(splitter, stretch=1)

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
    # Import-handlers
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
    # Publieke interface — metadata
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

    # ------------------------------------------------------------------
    # Publieke interface — projectenlijst
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
