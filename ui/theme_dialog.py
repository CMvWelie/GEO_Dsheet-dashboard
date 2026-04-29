"""Dialoog voor het aanmaken van een eigen UI-template."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class ColorField(QGroupBox):
    """Compact kleurveld met hex-input en kleurkiezer."""

    def __init__(self, label: str, value: str, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(label)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.edit = QLineEdit(value)
        self.edit.setMaxLength(7)
        self.swatch = QLabel()
        self.swatch.setFixedWidth(28)
        self.button = QPushButton('Kies')
        self.button.clicked.connect(self._choose)
        self.edit.textChanged.connect(self._update_swatch)
        layout.addWidget(self.edit)
        layout.addWidget(self.swatch)
        layout.addWidget(self.button)
        self._update_swatch(value)

    def value(self) -> str:
        text = self.edit.text().strip()
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', text):
            raise ValueError(f'Ongeldige kleur: {text}')
        return text.upper()

    def _choose(self) -> None:
        color = QColorDialog.getColor(QColor(self.edit.text()), self, 'Kies kleur')
        if color.isValid():
            self.edit.setText(color.name().upper())

    def _update_swatch(self, value: str) -> None:
        color = value if re.fullmatch(r'#[0-9A-Fa-f]{6}', value.strip()) else '#FFFFFF'
        self.swatch.setStyleSheet(f'background:{color}; border:1px solid #888;')


class ThemeTemplateDialog(QDialog):
    """Laat een gebruiker een themebestand invullen en opslaan."""

    def __init__(self, themes_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._themes_dir = themes_dir
        self.created_theme_name: str = ''
        self.setWindowTitle('Eigen template maken')
        self.setMinimumWidth(620)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Bijvoorbeeld: Mijn Bureau')
        self.font_combo = QFontComboBox()
        form.addRow('Templatenaam', self.name_edit)
        form.addRow('Lettertype', self.font_combo)
        root.addLayout(form)

        colors = QGroupBox('Kleuren')
        color_layout = QFormLayout(colors)
        self.primary = ColorField('Hoofdkleur / tabelkop', '#147ACF')
        self.text = ColorField('Tekstkleur', '#44546A')
        self.border = ColorField('Randkleur tabellen', '#000000')
        self.even_row = ColorField('Afwisselende tabelrij', '#F2F2F2')
        self.background = ColorField('Achtergrond app', '#FAFBFC')
        color_layout.addRow(self.primary)
        color_layout.addRow(self.text)
        color_layout.addRow(self.border)
        color_layout.addRow(self.even_row)
        color_layout.addRow(self.background)
        root.addWidget(colors)

        headings = QGroupBox('Kopstijlen')
        heading_layout = QFormLayout(headings)
        self.h1_size = QSpinBox()
        self.h1_size.setRange(10, 28)
        self.h1_size.setValue(14)
        self.h1_bold = QCheckBox('Vet')
        self.h1_bold.setChecked(True)
        h1_row = QHBoxLayout()
        h1_row.addWidget(self.h1_size)
        h1_row.addWidget(self.h1_bold)
        h1_row.addStretch()

        self.h2_size = QSpinBox()
        self.h2_size.setRange(8, 22)
        self.h2_size.setValue(12)
        self.h2_bold = QCheckBox('Vet')
        self.h2_bold.setChecked(True)
        h2_row = QHBoxLayout()
        h2_row.addWidget(self.h2_size)
        h2_row.addWidget(self.h2_bold)
        h2_row.addStretch()

        heading_layout.addRow('Kop 1 grootte', h1_row)
        heading_layout.addRow('Kop 2 grootte', h2_row)
        root.addWidget(headings)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Eigen template', 'Vul een templatenaam in.')
            return
        if name.lower() in {'dkib', 'sixgeoconsult', 'basic'}:
            QMessageBox.warning(
                self,
                'Eigen template',
                'Gebruik een andere naam; DKIB, SixGeoConsult en Basic zijn standaardstijlen.',
            )
            return

        try:
            primary = self.primary.value()
            text = self.text.value()
            border = self.border.value()
            even_row = self.even_row.value()
            background = self.background.value()
        except ValueError as exc:
            QMessageBox.warning(self, 'Eigen template', str(exc))
            return

        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') or 'custom'
        path = self._themes_dir / f'{slug}.json'
        if path.exists():
            QMessageBox.warning(
                self,
                'Eigen template',
                f'Er bestaat al een templatebestand met de naam {path.name}.',
            )
            return

        font = self.font_combo.currentFont().family()
        data = {
            'name': name,
            'colors': {
                'primary': primary,
                'primary_hover': _shade(primary, 0.82),
                'primary_pressed': _shade(primary, 0.64),
                'text': text,
                'text_muted': '#7A8794',
                'border': _lighten(border, 0.82),
                'border_strong': border,
                'surface': '#FFFFFF',
                'background': background,
                'ok': '#309942',
                'warning': '#FF5C00',
                'danger': '#C0392B',
            },
            'typography': {
                'family': font,
                'fallback': 'Segoe UI',
                'size_base': 11,
                'size_title': self.h2_size.value(),
                'size_small': 10,
            },
            'geometry': {
                'radius': 4,
                'spacing': 8,
                'padding_button': '7px 14px',
            },
            'table': {
                'header_bg': primary,
                'header_fg': '#FFFFFF',
                'subheader_bg': primary,
                'subheader_fg': '#FFFFFF',
                'border': border,
                'row_odd_bg': '#FFFFFF',
                'row_even_bg': even_row,
                'label_color': '#000000',
                'value_color': '#000000',
                'extra_color': '#000000',
            },
            'headings': {
                'h1_size': self.h1_size.value(),
                'h1_weight': 700 if self.h1_bold.isChecked() else 500,
                'h1_color': primary,
                'h2_size': self.h2_size.value(),
                'h2_weight': 600 if self.h2_bold.isChecked() else 500,
                'h2_color': text,
            },
            'assets': {
                'font_files': [],
                'app_logo': '',
            },
        }

        self._themes_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        self.created_theme_name = name
        self.accept()


def _shade(hex_color: str, factor: float) -> str:
    r, g, b = _rgb(hex_color)
    return f'#{int(r * factor):02X}{int(g * factor):02X}{int(b * factor):02X}'


def _lighten(hex_color: str, factor: float) -> str:
    r, g, b = _rgb(hex_color)
    return (
        f'#{int(r + (255 - r) * factor):02X}'
        f'{int(g + (255 - g) * factor):02X}'
        f'{int(b + (255 - b) * factor):02X}'
    )


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip('#')
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
