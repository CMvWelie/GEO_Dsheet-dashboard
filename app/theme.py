"""Thema-systeem voor de UI (pure Python, geen Qt-imports).

Een Theme bestaat uit een naam, kleuren, typografie, geometrie en assets.
Wordt geladen vanuit JSON-bestand en kan een Qt-stylesheet-string genereren.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


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
class Theme:
    """Volledige thema-definitie."""
    name: str
    colors: ThemeColors
    typography: ThemeTypography
    geometry: ThemeGeometry
    assets: ThemeAssets

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

        return cls(
            name=str(data.get('name', path.stem)),
            colors=colors,
            typography=typography,
            geometry=geometry,
            assets=assets,
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
        return []

    gevonden: list[tuple[str, Path]] = []
    for pad in sorted(themes_dir.glob('*.json')):
        try:
            thema = Theme.load(pad)
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        gevonden.append((thema.name, pad))

    gevonden.sort(key=lambda paar: paar[0])
    return gevonden
