"""Dialoog voor het aanmaken van een eigen UI-template."""

from __future__ import annotations

import json
import re
from pathlib import Path

from PyQt6.QtGui import QColor, QFont
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

    def set_value(self, value: str) -> None:
        self.edit.setText(value)

    def _choose(self) -> None:
        color = QColorDialog.getColor(QColor(self.edit.text()), self, 'Kies kleur')
        if color.isValid():
            self.edit.setText(color.name().upper())

    def _update_swatch(self, value: str) -> None:
        color = value if re.fullmatch(r'#[0-9A-Fa-f]{6}', value.strip()) else '#FFFFFF'
        self.swatch.setStyleSheet(f'background:{color}; border:1px solid #888;')


class ThemeTemplateDialog(QDialog):
    """Laat een gebruiker een themebestand invullen en opslaan."""

    def __init__(
        self,
        themes_dir: Path,
        parent=None,
        theme_path: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self._themes_dir = themes_dir
        self._theme_path = theme_path
        self._edit_data: dict | None = None
        self._original_font_family: str = ''
        self._preserve_original_font: bool = False
        self.created_theme_name: str = ''
        self.setWindowTitle('Template tunen' if theme_path else 'Eigen template maken')
        self.setMinimumWidth(620)
        self._build()
        if theme_path is not None:
            self._load_existing(theme_path)

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

        typography = QGroupBox('Tekstgroottes')
        typography_layout = QFormLayout(typography)
        self.body_text_size = QSpinBox()
        self.body_text_size.setRange(6, 18)
        self.body_text_size.setValue(11)
        self.table_text_size = QSpinBox()
        self.table_text_size.setRange(5, 14)
        self.table_text_size.setValue(7)
        self.table_header_size = QSpinBox()
        self.table_header_size.setRange(5, 16)
        self.table_header_size.setValue(8)
        typography_layout.addRow('Tekst buiten tabellen', self.body_text_size)
        typography_layout.addRow('Tekst in tabellen', self.table_text_size)
        typography_layout.addRow('Tabelkoppen', self.table_header_size)
        root.addWidget(typography)

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
        is_edit = self._theme_path is not None
        if not is_edit and name.lower() in {'dkib', 'sixgeoconsult', 'basic'}:
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

        if is_edit:
            path = self._theme_path
        else:
            slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') or 'custom'
            path = self._themes_dir / f'{slug}.json'
        if not is_edit and path.exists():
            QMessageBox.warning(
                self,
                'Eigen template',
                f'Er bestaat al een templatebestand met de naam {path.name}.',
            )
            return

        if self._preserve_original_font and self._original_font_family:
            font = self._original_font_family
        else:
            font = self.font_combo.currentFont().family()
        data = self._edit_data.copy() if self._edit_data is not None else {}
        data['name'] = name

        colors = data.setdefault('colors', {})
        colors.update({
            'primary': primary,
            'primary_hover': _shade(primary, 0.82),
            'primary_pressed': _shade(primary, 0.64),
            'text': text,
            'text_muted': colors.get('text_muted', '#7A8794'),
            'border': _lighten(border, 0.82),
            'border_strong': border,
            'surface': colors.get('surface', '#FFFFFF'),
            'background': background,
            'ok': colors.get('ok', '#309942'),
            'warning': colors.get('warning', '#FF5C00'),
            'danger': colors.get('danger', '#C0392B'),
        })

        typography = data.setdefault('typography', {})
        typography.update({
            'family': font,
            'fallback': typography.get('fallback', 'Segoe UI'),
            'size_base': typography.get('size_base', 11),
            'size_title': self.h2_size.value(),
            'size_small': typography.get('size_small', 10),
            'size_text': self.body_text_size.value(),
            'size_table': self.table_text_size.value(),
            'size_table_header': self.table_header_size.value(),
        })

        data.setdefault('geometry', {
            'radius': 4,
            'spacing': 8,
            'padding_button': '7px 14px',
        })

        table = data.setdefault('table', {})
        table.update({
            'header_bg': primary,
            'header_fg': table.get('header_fg', '#FFFFFF'),
            'subheader_bg': primary,
            'subheader_fg': table.get('subheader_fg', '#FFFFFF'),
            'border': border,
            'row_odd_bg': table.get('row_odd_bg', '#FFFFFF'),
            'row_even_bg': even_row,
            'label_color': table.get('label_color', '#000000'),
            'value_color': table.get('value_color', '#000000'),
            'extra_color': table.get('extra_color', '#000000'),
        })

        headings = data.setdefault('headings', {})
        headings.update({
            'h1_size': self.h1_size.value(),
            'h1_weight': 700 if self.h1_bold.isChecked() else 500,
            'h1_color': primary,
            'h2_size': self.h2_size.value(),
            'h2_weight': 600 if self.h2_bold.isChecked() else 500,
            'h2_color': text,
        })

        data.setdefault('assets', {
            'font_files': [],
            'app_logo': '',
        })

        self._themes_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        self.created_theme_name = name
        self.accept()

    def _load_existing(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, 'Template tunen', f'Template laden mislukt:\n{exc}')
            return

        self._edit_data = data
        self.name_edit.setText(str(data.get('name', path.stem)))
        self.name_edit.setReadOnly(True)

        colors = data.get('colors') or {}
        table = data.get('table') or {}
        typography = data.get('typography') or {}
        headings = data.get('headings') or {}

        self._original_font_family = str(typography.get('family', 'Segoe UI'))
        self.font_combo.setCurrentFont(QFont(self._original_font_family))
        self._preserve_original_font = (
            self.font_combo.currentFont().family().lower()
            != self._original_font_family.lower()
        )
        self.primary.set_value(str(colors.get('primary', '#147ACF')))
        self.text.set_value(str(colors.get('text', '#44546A')))
        self.border.set_value(str(table.get('border', colors.get('border_strong', '#000000'))))
        self.even_row.set_value(str(table.get('row_even_bg', '#F2F2F2')))
        self.background.set_value(str(colors.get('background', '#FAFBFC')))

        self.h1_size.setValue(int(headings.get('h1_size', 14)))
        self.h1_bold.setChecked(int(headings.get('h1_weight', 700)) >= 600)
        self.h2_size.setValue(int(headings.get('h2_size', typography.get('size_title', 12))))
        self.h2_bold.setChecked(int(headings.get('h2_weight', 600)) >= 600)
        self.body_text_size.setValue(int(typography.get('size_text', typography.get('size_base', 11))))
        self.table_text_size.setValue(int(typography.get('size_table', 7)))
        self.table_header_size.setValue(int(typography.get('size_table_header', 8)))


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
