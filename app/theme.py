"""Thema-systeem voor de UI (pure Python, geen Qt-imports).

Een Theme bestaat uit een naam, kleuren, typografie, geometrie en assets.
Wordt geladen vanuit JSON-bestand en kan een Qt-stylesheet-string genereren.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

BASIC_THEME_NAME = 'Basic'


@dataclass
class ThemeColors:
    """Kleurpalet voor het thema."""
    primary: str
    primary_hover: str
    primary_pressed: str
    text: str
    text_muted: str
    border: str
    border_strong: str
    surface: str
    background: str
    ok: str
    warning: str
    danger: str


@dataclass
class ThemeTypography:
    """Typografie-instellingen."""
    family: str
    fallback: str
    size_base: int
    size_title: int
    size_small: int


@dataclass
class ThemeGeometry:
    """Geometrie-instellingen (radii, spacings)."""
    radius: int
    spacing: int
    padding_button: str


@dataclass
class ThemeAssets:
    """Asset-paden (fonts, logos)."""
    font_files: list[str] = field(default_factory=list)
    app_logo: str = ''


@dataclass
class ThemeTableStyle:
    """Tabelkleuren en -typografie voor applicatietabellen."""
    header_bg: str = ''
    header_fg: str = '#FFFFFF'
    subheader_bg: str = ''
    subheader_fg: str = '#FFFFFF'
    border: str = '#000000'
    row_odd_bg: str = '#FFFFFF'
    row_even_bg: str = '#F2F2F2'
    label_color: str = '#000000'
    value_color: str = '#000000'
    extra_color: str = '#000000'


@dataclass
class ThemeHeadingStyle:
    """Kopstijlen voor app-secties en kaartkoppen."""
    h1_size: int = 14
    h1_weight: int = 700
    h1_color: str = ''
    h2_size: int = 12
    h2_weight: int = 600
    h2_color: str = ''


@dataclass
class Theme:
    """Volledige thema-definitie."""
    name: str
    colors: ThemeColors
    typography: ThemeTypography
    geometry: ThemeGeometry
    assets: ThemeAssets
    table: ThemeTableStyle = field(default_factory=ThemeTableStyle)
    headings: ThemeHeadingStyle = field(default_factory=ThemeHeadingStyle)

    def build_stylesheet(self, font_family: str) -> str:
        """Genereer een Qt-QSS-string voor dit thema.

        Parameters
        ----------
        font_family:
            De werkelijke font-familienaam zoals Qt deze rapporteert na
            ``QFontDatabase.addApplicationFont()``. Kan afwijken van
            ``typography.family`` in het JSON-bestand.

        Returns
        -------
        str
            Een complete QSS-string voor ``QApplication.setStyleSheet()``.
        """
        c = self.colors
        t = self.typography
        g = self.geometry
        ff = f'"{font_family}"'

        return f"""
* {{
    font-family: {ff}, "{t.fallback}", sans-serif;
    font-size: {t.size_base}pt;
    color: {c.text};
}}

QWidget {{
    background: {c.background};
}}

QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPlainTextEdit, QTextEdit {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    padding: 3px 6px;
    color: {c.text};
}}

QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {c.primary};
}}

QGroupBox {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius + 2}px;
    margin-top: 10px;
    padding: 10px 8px 6px 8px;
    font-weight: 600;
    color: {c.primary};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: {c.primary};
    font-size: {t.size_title}pt;
}}

QPushButton {{
    background: {c.surface};
    color: {c.text};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    padding: {g.padding_button};
    font-size: {t.size_base}pt;
    font-weight: 500;
}}

QPushButton:hover {{
    background: {c.background};
    border: 1px solid {c.border_strong};
}}

QPushButton:pressed {{
    background: {c.border};
}}

QPushButton:disabled {{
    color: {c.text_muted};
    background: {c.background};
    border: 1px solid {c.border};
}}

QPushButton#btnPrimary {{
    background: {c.primary};
    color: {c.surface};
    border: 1px solid {c.primary_hover};
    font-weight: 600;
}}

QPushButton#btnPrimary:hover {{
    background: {c.primary_hover};
}}

QPushButton#btnPrimary:pressed {{
    background: {c.primary_pressed};
}}

QPushButton#btnDanger {{
    background: {c.surface};
    color: {c.danger};
    border: 1px solid {c.danger};
}}

QPushButton#btnDanger:hover {{
    background: #fdf0ee;
}}

QPushButton#btnNormal {{
    background: {c.surface};
    color: {c.text};
    border: 1px solid {c.border};
}}

QPushButton#btnClear {{
    background: {c.surface};
    color: {c.text_muted};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    font-size: {t.size_small}pt;
    padding: 2px 4px;
}}

QPushButton#btnClear:hover {{
    color: {c.danger};
    border-color: {c.danger};
}}

QPushButton#btnToggle {{
    background: {c.surface};
    color: {c.text};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    font-size: {t.size_small}pt;
    font-weight: 600;
    padding: 2px 6px;
}}

QPushButton#btnToggle:hover {{
    background: {c.background};
    border-color: {c.border_strong};
}}

QPushButton#btnToggle:checked {{
    background: {c.primary};
    color: {c.surface};
    border-color: {c.primary_hover};
}}

QPushButton#btnTool {{
    background: {c.background};
    color: {c.text};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    font-size: {t.size_small}pt;
    font-weight: 600;
    padding: 6px;
    text-align: center;
}}

QPushButton#btnTool:hover {{
    background: {c.surface};
    border-color: {c.border_strong};
}}

QPushButton#btnWarning {{
    background: {c.surface};
    color: {c.warning};
    border: 1px solid {c.warning};
    border-radius: {g.radius}px;
    font-size: {t.size_small}pt;
    padding: 5px 10px;
}}

QPushButton#btnWarning:hover {{
    background: {c.background};
}}

QTabWidget::pane {{
    border-top: 1px solid {c.border};
    background: {c.surface};
    top: -1px;
}}

QTabBar::tab {{
    background: {c.background};
    color: {c.text};
    padding: 6px 14px;
    border: 1px solid {c.border};
    border-bottom: none;
    border-top-left-radius: {g.radius}px;
    border-top-right-radius: {g.radius}px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {c.surface};
    color: {c.primary};
    border-top: 3px solid {c.primary};
    font-weight: 600;
}}

QTabBar::tab:!selected:hover {{
    background: {c.surface};
}}

QListWidget {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
}}

QListWidget::item:selected {{
    background: {c.primary};
    color: {c.surface};
}}

QLabel {{
    background: transparent;
    color: {c.text};
}}

QLabel#hintLabel {{
    color: {c.text_muted};
    font-size: {t.size_small}pt;
    font-style: italic;
}}

        QLabel#projectLabel {{
            font-size: {t.size_small}pt;
            font-weight: 600;
            color: {c.text};
        }}

        QLabel#heading1 {{
            font-size: {self.headings.h1_size}pt;
            font-weight: {self.headings.h1_weight};
            color: {self.headings.h1_color or c.primary};
            background: transparent;
        }}

        QLabel#heading2 {{
            font-size: {self.headings.h2_size}pt;
            font-weight: {self.headings.h2_weight};
            color: {self.headings.h2_color or c.text};
            background: transparent;
        }}

QScrollBar:vertical {{
    background: {c.background};
    width: 8px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {c.border_strong};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c.primary};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    width: 0;
    border: none;
    background: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {c.background};
    height: 8px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {c.border_strong};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c.primary};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    height: 0;
    border: none;
    background: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
    background: {c.surface};
    border-top-right-radius: {g.radius}px;
    border-bottom-right-radius: {g.radius}px;
}}

QComboBox::drop-down:hover {{
    background: {c.background};
    border: none;
    border-left: 1px solid {c.border_strong};
    border-top-right-radius: {g.radius}px;
    border-bottom-right-radius: {g.radius}px;
}}

QComboBox::down-arrow {{
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5' viewBox='0 0 8 5'><polygon points='0,0 8,0 4,5' fill='%23{c.text[1:]}'/></svg>");
    width: 8px;
    height: 5px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    width: 16px;
    background: {c.background};
    border: none;
    border-left: 1px solid {c.border};
    border-bottom: 1px solid {c.border};
    border-top-right-radius: {g.radius}px;
    subcontrol-position: top right;
    subcontrol-origin: border;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 16px;
    background: {c.background};
    border: none;
    border-left: 1px solid {c.border};
    border-bottom-right-radius: {g.radius}px;
    subcontrol-position: bottom right;
    subcontrol-origin: border;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {c.primary};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5' viewBox='0 0 8 5'><polygon points='0,5 8,5 4,0' fill='%23{c.text[1:]}'/></svg>");
    width: 8px;
    height: 5px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5' viewBox='0 0 8 5'><polygon points='0,0 8,0 4,5' fill='%23{c.text[1:]}'/></svg>");
    width: 8px;
    height: 5px;
}}

QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {{
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5' viewBox='0 0 8 5'><polygon points='0,5 8,5 4,0' fill='white'/></svg>");
}}

QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {{
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5' viewBox='0 0 8 5'><polygon points='0,0 8,0 4,5' fill='white'/></svg>");
}}

QTabBar QToolButton {{
    background: {c.surface};
    border: 1px solid {c.border};
    border-radius: {g.radius}px;
    padding: 2px 4px;
}}

QTabBar QToolButton:hover {{
    background: {c.background};
    border-color: {c.border_strong};
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {c.border};
    border-radius: 3px;
    background: {c.surface};
}}

QCheckBox::indicator:hover {{
    border-color: {c.border_strong};
}}

QCheckBox::indicator:checked {{
    background: {c.primary};
    border: 1px solid {c.primary_hover};
    image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='9' viewBox='0 0 12 9'><polyline points='1,4 4,8 11,1' stroke='white' stroke-width='2' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>");
}}

QCheckBox::indicator:checked:hover {{
    background: {c.primary_hover};
    border: 1px solid {c.primary_pressed};
}}
        """.strip()

    @classmethod
    def load(cls, path: Path) -> 'Theme':
        """Laad een thema vanuit een JSON-bestand.

        Parameters
        ----------
        path:
            Pad naar het JSON-themabestand.

        Returns
        -------
        Theme
            Het geladen thema.

        Raises
        ------
        ValueError
            Als een verplichte sectie ontbreekt of een verplicht veld binnen een sectie.
        """
        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        for vereist in ('colors', 'typography', 'geometry'):
            if vereist not in data:
                raise ValueError(f"Themabestand mist verplichte sectie '{vereist}'")

        try:
            colors = ThemeColors(**data['colors'])
            typography = ThemeTypography(**data['typography'])
            geometry = ThemeGeometry(**data['geometry'])
        except TypeError as exc:
            raise ValueError(f'Ongeldige thema-inhoud: {exc}') from exc

        assets_data = data.get('assets') or {}
        assets = ThemeAssets(
            font_files=list(assets_data.get('font_files', [])),
            app_logo=assets_data.get('app_logo', ''),
        )
        table_data = data.get('table') or {}
        headings_data = data.get('headings') or {}

        primary = colors.primary
        table = ThemeTableStyle(
            header_bg=table_data.get('header_bg', primary),
            header_fg=table_data.get('header_fg', '#FFFFFF'),
            subheader_bg=table_data.get('subheader_bg', table_data.get('header_bg', primary)),
            subheader_fg=table_data.get('subheader_fg', table_data.get('header_fg', '#FFFFFF')),
            border=table_data.get('border', '#000000'),
            row_odd_bg=table_data.get('row_odd_bg', colors.surface),
            row_even_bg=table_data.get('row_even_bg', '#F2F2F2'),
            label_color=table_data.get('label_color', '#000000'),
            value_color=table_data.get('value_color', '#000000'),
            extra_color=table_data.get('extra_color', '#000000'),
        )
        headings = ThemeHeadingStyle(
            h1_size=int(headings_data.get('h1_size', 14)),
            h1_weight=int(headings_data.get('h1_weight', 700)),
            h1_color=headings_data.get('h1_color', colors.primary),
            h2_size=int(headings_data.get('h2_size', 12)),
            h2_weight=int(headings_data.get('h2_weight', 600)),
            h2_color=headings_data.get('h2_color', colors.text),
        )

        return cls(
            name=str(data.get('name', path.stem)),
            colors=colors,
            typography=typography,
            geometry=geometry,
            assets=assets,
            table=table,
            headings=headings,
        )


def discover_themes(themes_dir: Path) -> list[tuple[str, Path]]:
    """Vind alle geldige thema-JSON-bestanden in een directory.

    Parameters
    ----------
    themes_dir:
        Map om te scannen op ``*.json``-themabestanden.

    Returns
    -------
    list[tuple[str, Path]]
        Lijst van (naam, pad)-paren, gesorteerd op naam.
        Bestanden die niet als geldig thema kunnen worden geladen worden overgeslagen.
    """
    if not themes_dir.exists():
        return [(BASIC_THEME_NAME, Path())]

    gevonden: list[tuple[str, Path]] = []
    for pad in sorted(themes_dir.glob('*.json')):
        try:
            thema = Theme.load(pad)
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        gevonden.append((thema.name, pad))

    if not any(naam == BASIC_THEME_NAME for naam, _pad in gevonden):
        gevonden.append((BASIC_THEME_NAME, Path()))

    gevonden.sort(key=lambda paar: paar[0])
    return gevonden


def create_basic_theme() -> Theme:
    """Maak een ingebouwde fallbackstijl zonder afhankelijkheid van JSON-bestanden."""
    colors = ThemeColors(
        primary='#C8C8C8',
        primary_hover='#B4B4B4',
        primary_pressed='#A0A0A0',
        text='#111827',
        text_muted='#6B7280',
        border='#C8C8C8',
        border_strong='#A0A0A0',
        surface='#FFFFFF',
        background='#F4F4F4',
        ok='#309942',
        warning='#FF5C00',
        danger='#C0392B',
    )
    typography = ThemeTypography(
        family='Segoe UI',
        fallback='Arial',
        size_base=11,
        size_title=12,
        size_small=10,
    )
    geometry = ThemeGeometry(radius=4, spacing=8, padding_button='7px 14px')
    table = ThemeTableStyle(
        header_bg='#C8C8C8',
        header_fg='#111827',
        subheader_bg='#C8C8C8',
        subheader_fg='#111827',
        border='#C8C8C8',
        row_odd_bg='#FFFFFF',
        row_even_bg='#F4F4F4',
        label_color='#111827',
        value_color='#111827',
        extra_color='#374151',
    )
    headings = ThemeHeadingStyle(
        h1_size=14,
        h1_weight=700,
        h1_color='#111827',
        h2_size=12,
        h2_weight=600,
        h2_color='#111827',
    )
    return Theme(
        name=BASIC_THEME_NAME,
        colors=colors,
        typography=typography,
        geometry=geometry,
        assets=ThemeAssets(),
        table=table,
        headings=headings,
    )
