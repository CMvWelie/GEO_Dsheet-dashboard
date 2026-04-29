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
        """Placeholder — geïmplementeerd in Task 4."""
        return ''

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
