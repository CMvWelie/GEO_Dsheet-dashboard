"""Tab Instellingen — persistente app-instellingen, template-keuze en preview-opener."""

from __future__ import annotations
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QComboBox, QDialog, QMessageBox,
    QTabWidget,
)
from PyQt6.QtCore import pyqtSignal

from app.theme_apply import THEMES_DIR
from parsers.models import Project
from ui.tabs.tab_debug import TabDebug
from ui.theme_dialog import ThemeTemplateDialog


class TabInstellingen(QWidget):
    """Tabblad met persistente applicatie-instellingen (Tab Instellingen)."""

    import_map_changed = pyqtSignal(str)
    """Afgegeven zodra de standaard importmap wijzigt (ook bij wissen)."""

    theme_selected = pyqtSignal(str)
    """Afgegeven zodra de gebruiker op 'Toepassen' klikt voor een ander UI-thema."""

    theme_created = pyqtSignal(str)
    """Afgegeven zodra een eigen templatebestand is aangemaakt."""

    theme_updated = pyqtSignal(str)
    """Afgegeven zodra een bestaand templatebestand is aangepast."""

    theme_delete_requested = pyqtSignal(str)
    """Afgegeven zodra de gebruiker een custom template wil verwijderen."""

    restart_requested = pyqtSignal()
    """Afgegeven zodra de gebruiker op 'Applicatie herstarten' klikt."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._huidig_thema_naam: str = ''
        self._beschikbare_themas: list[tuple[str, Path]] = []
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sub_tabs = QTabWidget()
        self._sub_tabs.addTab(self._build_algemeen_tab(), 'Algemeen')

        self._tab_debug = TabDebug()
        self._sub_tabs.addTab(self._tab_debug, 'Debug')

        root.addWidget(self._sub_tabs)

    def _build_algemeen_tab(self) -> QWidget:
        """Bouw de Algemeen-subtab met thema-, import- en applicatie-groepen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Groep: Template (UI-thema) ────────────────────────────────
        layout.addWidget(self._build_template_group())

        # ── Groep: Import-instellingen ────────────────────────────────
        imp_box = QGroupBox('Import-instellingen')
        imp_vl = QVBoxLayout(imp_box)
        imp_vl.setSpacing(6)

        imp_lbl = QLabel('Standaard importmap')
        imp_lbl.setObjectName('hintLabel')

        imp_rij = QHBoxLayout()
        self._import_map_edit = QLineEdit()
        self._import_map_edit.setPlaceholderText('Map om import-dialoog in te openen… (optioneel)')
        self._import_map_edit.textChanged.connect(self.import_map_changed)

        imp_bladeren_btn = QPushButton('Bladeren…')
        imp_bladeren_btn.setObjectName('btnNormal')
        imp_bladeren_btn.clicked.connect(self._on_bladeren_importmap)

        imp_wis_btn = QPushButton('✕')
        imp_wis_btn.setObjectName('btnClear')
        imp_wis_btn.setFixedWidth(28)
        imp_wis_btn.setToolTip('Verwijder standaard importmap')
        imp_wis_btn.clicked.connect(self._on_wis_importmap)

        imp_rij.addWidget(self._import_map_edit)
        imp_rij.addWidget(imp_bladeren_btn)
        imp_rij.addWidget(imp_wis_btn)

        imp_hint = QLabel('Het importeer-dialoogvenster opent voortaan in deze map')
        imp_hint.setObjectName('hintLabel')

        imp_vl.addWidget(imp_lbl)
        imp_vl.addLayout(imp_rij)
        imp_vl.addWidget(imp_hint)
        layout.addWidget(imp_box)

        # ── Groep: Applicatie ─────────────────────────────────────────
        layout.addWidget(self._build_applicatie_group())

        layout.addStretch()
        return widget

    def _build_applicatie_group(self) -> QGroupBox:
        """Bouw de Applicatie-groep met de Herstart-knop."""
        box = QGroupBox('Applicatie')
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        rij = QHBoxLayout()
        self._restart_btn = QPushButton('Applicatie herstarten')
        self._restart_btn.setObjectName('btnNormal')
        self._restart_btn.clicked.connect(self._on_restart)
        rij.addWidget(self._restart_btn)
        rij.addStretch()
        vl.addLayout(rij)

        hint = QLabel('Sluit het venster en start de applicatie opnieuw op.')
        hint.setObjectName('hintLabel')
        vl.addWidget(hint)
        return box

    def _build_template_group(self) -> QGroupBox:
        """Bouw de Template-groep (UI-thema-keuze).

        Returns
        -------
        QGroupBox
            De gevulde thema-keuzegroepdoos.
        """
        box = QGroupBox('Template (UI-thema)')
        vl = QVBoxLayout(box)
        vl.setSpacing(6)

        self._actief_label = QLabel('Actief: -')
        self._actief_label.setObjectName('hintLabel')
        vl.addWidget(self._actief_label)

        rij = QHBoxLayout()
        self._theme_combo = QComboBox()
        self._theme_combo.setMinimumWidth(220)
        self._theme_combo.currentTextChanged.connect(lambda _text: self._update_theme_buttons())
        rij.addWidget(self._theme_combo)

        self._theme_apply_btn = QPushButton('Toepassen')
        self._theme_apply_btn.setObjectName('btnPrimary')
        self._theme_apply_btn.clicked.connect(self._on_theme_apply)
        rij.addWidget(self._theme_apply_btn)

        self._theme_new_btn = QPushButton('Eigen template...')
        self._theme_new_btn.setObjectName('btnNormal')
        self._theme_new_btn.clicked.connect(self._on_theme_new)
        rij.addWidget(self._theme_new_btn)

        self._theme_tune_btn = QPushButton('Tunen...')
        self._theme_tune_btn.setObjectName('btnNormal')
        self._theme_tune_btn.clicked.connect(self._on_theme_tune)
        rij.addWidget(self._theme_tune_btn)

        self._theme_delete_btn = QPushButton('Verwijderen')
        self._theme_delete_btn.setObjectName('btnDanger')
        self._theme_delete_btn.clicked.connect(self._on_theme_delete)
        rij.addWidget(self._theme_delete_btn)
        rij.addStretch()
        vl.addLayout(rij)

        self._herstart_label = QLabel('Template wordt direct toegepast.')
        self._herstart_label.setObjectName('hintLabel')
        self._herstart_label.setVisible(False)
        vl.addWidget(self._herstart_label)

        return box

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_import_map(self, pad: str) -> None:
        """Toon een opgeslagen importmap zonder een signal af te geven.

        Parameters
        ----------
        pad:
            Te tonen mappad (leeg = veld wissen).
        """
        self._import_map_edit.blockSignals(True)
        self._import_map_edit.setText(pad)
        self._import_map_edit.blockSignals(False)

    def update_project(self, project: Project | None) -> None:
        """Propageer projectwijziging naar de Debug-subtab.

        Parameters
        ----------
        project:
            Actief project, of ``None`` als geen project geladen.
        """
        self._tab_debug.update_project(project)

    def set_themes(self, themas: list[tuple[str, Path]], actief_naam: str) -> None:
        """Vul de thema-dropdown en markeer het huidige actieve thema.

        Parameters
        ----------
        themas:
            Lijst van (naam, pad)-paren zoals teruggegeven door ``discover_themes()``.
        actief_naam:
            Naam van het thema dat momenteel actief is (verschijnt in 'Actief: …').
        """
        self._beschikbare_themas = themas
        self._huidig_thema_naam = actief_naam
        self._actief_label.setText(f'Actief: {actief_naam or "-"}')

        self._theme_combo.blockSignals(True)
        self._theme_combo.clear()
        idx_actief = -1
        for i, (naam, _pad) in enumerate(themas):
            self._theme_combo.addItem(naam)
            if naam == actief_naam:
                idx_actief = i
        if idx_actief >= 0:
            self._theme_combo.setCurrentIndex(idx_actief)
        elif self._theme_combo.count() > 0:
            self._theme_combo.setCurrentIndex(0)
        self._theme_combo.blockSignals(False)
        self._update_theme_buttons()

        self._herstart_label.setVisible(False)

    # ------------------------------------------------------------------
    # Privé handlers
    # ------------------------------------------------------------------

    def _on_restart(self) -> None:
        """Vraag bevestiging en geef herstart-verzoek door aan het hoofdvenster."""
        antwoord = QMessageBox.question(
            self,
            'Applicatie herstarten',
            'De applicatie wordt afgesloten en opnieuw opgestart. Doorgaan?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if antwoord == QMessageBox.StandardButton.Yes:
            self.restart_requested.emit()

    def _on_bladeren_importmap(self) -> None:
        map_pad = QFileDialog.getExistingDirectory(
            self, 'Selecteer standaard importmap',
            self._import_map_edit.text() or '',
        )
        if map_pad:
            self._import_map_edit.setText(map_pad)

    def _on_wis_importmap(self) -> None:
        self._import_map_edit.clear()

    def _on_theme_apply(self) -> None:
        """Gebruiker klikt 'Toepassen' op de thema-dropdown."""
        gekozen = self._theme_combo.currentText()
        if not gekozen:
            return
        self._herstart_label.setVisible(True)
        self.theme_selected.emit(gekozen)

    def _on_theme_new(self) -> None:
        """Open dialoog om een eigen template te maken."""
        dlg = ThemeTemplateDialog(THEMES_DIR, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.created_theme_name:
            self.theme_created.emit(dlg.created_theme_name)

    def _on_theme_tune(self) -> None:
        """Open dialoog om het gekozen templatebestand te tunen."""
        gekozen = self._theme_combo.currentText()
        pad = self._theme_path_for_name(gekozen)
        if not gekozen or pad is None:
            return
        dlg = ThemeTemplateDialog(THEMES_DIR, self, theme_path=pad)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.created_theme_name:
            self.theme_updated.emit(dlg.created_theme_name)

    def _on_theme_delete(self) -> None:
        """Vraag bevestiging en geef delete-request door aan het hoofdvenster."""
        gekozen = self._theme_combo.currentText()
        if not gekozen or not self._is_custom_theme(gekozen):
            return
        antwoord = QMessageBox.question(
            self,
            'Template verwijderen',
            f'Custom template "{gekozen}" verwijderen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if antwoord == QMessageBox.StandardButton.Yes:
            self.theme_delete_requested.emit(gekozen)

    def _update_theme_buttons(self) -> None:
        gekozen = self._theme_combo.currentText()
        self._theme_delete_btn.setEnabled(self._is_custom_theme(gekozen))
        self._theme_tune_btn.setEnabled(self._theme_path_for_name(gekozen) is not None)

    def _theme_path_for_name(self, naam: str) -> Path | None:
        for theme_name, pad in self._beschikbare_themas:
            if theme_name == naam and pad:
                return pad
        return None

    @staticmethod
    def _is_custom_theme(naam: str) -> bool:
        if not naam:
            return False
        return naam.lower() not in {'dkib', 'sixgeoconsult', 'basic'}
