"""Linker zijbalk: bestandsimport, projectselectie en fase-selectie."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.file_list_widget import FileListWidget


class StatusLabel(QLabel):
    """Gekleurde statusbadge (OK / WARN / ERR)."""

    _COLORS = {
        'ok': ('#2f7d32', '#eef8ef', '#9ac89c'),
        'warn': ('#b26a00', '#fff7eb', '#e2be83'),
        'err': ('#b42318', '#fff2f1', '#e5a6a1'),
        'idle': ('#555555', '#f4f4f4', '#cccccc'),
    }

    def set_status(self, status_type: str, text: str, detail: str = '') -> None:
        """Stel de statustekst en kleur in.

        Parameters
        ----------
        status_type: 'ok', 'warn', 'err' of 'idle'.
        text:        Korte statustekst.
        detail:      Optionele detailtekst als tooltip.
        """
        fg, bg, border = self._COLORS.get(status_type, self._COLORS['idle'])
        self.setStyleSheet(
            f'color: {fg}; background: {bg}; border: 1px solid {border};'
            f'border-radius: 8px; padding: 4px 8px; font-weight: bold; font-size: 12px;'
        )
        self.setText(text)
        if detail:
            self.setToolTip(detail)


class Sidebar(QWidget):
    """Linker paneel met bestandsimport, project- en fase-selectie.

    Signals
    -------
    import_requested:    Gebruiker wil bestanden importeren.
    process_requested:   Gebruiker wil bestanden verwerken.
    reset_requested:     Gebruiker wil alles resetten.
    project_changed:     Ander project geselecteerd (waarde = base_name).
    stage_changed:       Andere fase geselecteerd (waarde = index).
    """

    import_requested = pyqtSignal()
    process_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    project_changed = pyqtSignal(str)
    stage_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Titel
        title = QLabel('<b>D-Sheet Dashboard</b>')
        title.setStyleSheet('font-size: 16px;')
        layout.addWidget(title)

        # Bestandsimport
        import_box = QGroupBox('Bestanden')
        import_layout = QVBoxLayout(import_box)

        btn_row = QWidget()
        btn_row_l = QHBoxLayout(btn_row)
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        self._import_btn = QPushButton('Importeer…')
        self._import_btn.clicked.connect(self.import_requested.emit)
        self._process_btn = QPushButton('Verwerk')
        self._process_btn.clicked.connect(self.process_requested.emit)
        self._reset_btn = QPushButton('Reset')
        self._reset_btn.clicked.connect(self.reset_requested.emit)
        btn_row_l.addWidget(self._import_btn)
        btn_row_l.addWidget(self._process_btn)
        btn_row_l.addWidget(self._reset_btn)
        import_layout.addWidget(btn_row)

        self._file_list = FileListWidget()
        import_layout.addWidget(self._file_list)
        layout.addWidget(import_box)

        # Project selectie
        proj_box = QGroupBox('Project')
        proj_layout = QVBoxLayout(proj_box)
        self._project_combo = QComboBox()
        self._project_combo.currentTextChanged.connect(self._on_project_changed)
        proj_layout.addWidget(self._project_combo)
        layout.addWidget(proj_box)

        # Fase selectie
        stage_box = QGroupBox('Bouwfase')
        stage_layout = QVBoxLayout(stage_box)
        self._stage_combo = QComboBox()
        self._stage_combo.currentIndexChanged.connect(self._on_stage_changed)
        stage_layout.addWidget(self._stage_combo)
        layout.addWidget(stage_box)

        # Status
        self._status = StatusLabel('Gereed')
        self._status.set_status('idle', 'Gereed', 'Importeer bestanden om te beginnen.')
        layout.addWidget(self._status)

        layout.addStretch()

    def _on_project_changed(self, text: str) -> None:
        if text:
            self.project_changed.emit(text)

    def _on_stage_changed(self, index: int) -> None:
        self.stage_changed.emit(index)

    def set_status(self, status_type: str, text: str, detail: str = '') -> None:
        """Delegeer naar StatusLabel."""
        self._status.set_status(status_type, text, detail)

    def set_files(self, files: dict[str, str]) -> None:
        """Vul de bestandslijst.

        Parameters
        ----------
        files: Dict filename → raw text.
        """
        self._file_list.set_files(files)

    def set_projects(self, project_names: dict[str, str]) -> None:
        """Vul de projectcombobox.

        Parameters
        ----------
        project_names: Dict base_name → projectnaam.
        """
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        for base_name, display_name in project_names.items():
            self._project_combo.addItem(display_name, userData=base_name)
        self._project_combo.blockSignals(False)
        if self._project_combo.count():
            self._on_project_changed(self._project_combo.currentData() or '')

    def set_stages(self, stage_names: list[str]) -> None:
        """Vul de fase-combobox.

        Parameters
        ----------
        stage_names: Lijst van fase-namen.
        """
        self._stage_combo.blockSignals(True)
        self._stage_combo.clear()
        for i, name in enumerate(stage_names):
            self._stage_combo.addItem(name)
        self._stage_combo.blockSignals(False)

    def active_project_key(self) -> str | None:
        """Geef de base_name van het geselecteerde project."""
        return self._project_combo.currentData()

    def active_stage_index(self) -> int:
        """Geef de index van de geselecteerde fase."""
        return max(0, self._stage_combo.currentIndex())
