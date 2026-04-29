"""Tab Instellingen — persistente app-instellingen, template-keuze en preview-opener."""

from __future__ import annotations
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QComboBox,
)
from PyQt6.QtCore import pyqtSignal


class TabInstellingen(QWidget):
    """Tabblad met persistente applicatie-instellingen (Tab Instellingen)."""

    template_path_changed = pyqtSignal(str)
    """Afgegeven zodra het Word-template-pad wijzigt (ook bij wissen)."""

    import_map_changed = pyqtSignal(str)
    """Afgegeven zodra de standaard importmap wijzigt (ook bij wissen)."""

    theme_selected = pyqtSignal(str)
    """Afgegeven zodra de gebruiker op 'Toepassen' klikt voor een ander UI-thema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._huidig_thema_naam: str = ''
        self._beschikbare_themas: list[tuple[str, Path]] = []
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        # ── Groep: Template (UI-thema) ────────────────────────────────
        root.addWidget(self._build_template_group())

        # ── Groep: Rapportage-instellingen ────────────────────────────
        tmpl_box = QGroupBox('Rapportage-instellingen')
        tmpl_vl = QVBoxLayout(tmpl_box)
        tmpl_vl.setSpacing(6)

        lbl = QLabel('Word-template (.dotx)')
        lbl.setObjectName('hintLabel')

        tmpl_rij = QHBoxLayout()
        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText('Pad naar .dotx template… (optioneel)')
        self._template_edit.textChanged.connect(self.template_path_changed)

        bladeren_btn = QPushButton('Bladeren…')
        bladeren_btn.setObjectName('btnNormal')
        bladeren_btn.clicked.connect(self._on_bladeren)

        wis_btn = QPushButton('✕')
        wis_btn.setObjectName('btnClear')
        wis_btn.setFixedWidth(28)
        wis_btn.setToolTip('Verwijder template-pad')
        wis_btn.clicked.connect(self._on_wis_template)

        tmpl_rij.addWidget(self._template_edit)
        tmpl_rij.addWidget(bladeren_btn)
        tmpl_rij.addWidget(wis_btn)

        hint = QLabel(
            'Optioneel — wordt ook gebruikt bij Word-export als het export-venster leeg is'
        )
        hint.setObjectName('hintLabel')

        tmpl_vl.addWidget(lbl)
        tmpl_vl.addLayout(tmpl_rij)
        tmpl_vl.addWidget(hint)
        root.addWidget(tmpl_box)

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
        root.addWidget(imp_box)

        root.addStretch()

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
        rij.addWidget(self._theme_combo)

        self._theme_apply_btn = QPushButton('Toepassen')
        self._theme_apply_btn.setObjectName('btnPrimary')
        self._theme_apply_btn.clicked.connect(self._on_theme_apply)
        rij.addWidget(self._theme_apply_btn)
        rij.addStretch()
        vl.addLayout(rij)

        self._herstart_label = QLabel('Wisseling actief na herstart van de app.')
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
        self._theme_combo.blockSignals(False)

        self._herstart_label.setVisible(False)

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
        if not gekozen or gekozen == self._huidig_thema_naam:
            return
        self._herstart_label.setVisible(True)
        self.theme_selected.emit(gekozen)
