"""Qt-aware bootstrap voor het thema-systeem.

Verantwoordelijk voor het registreren van fonts en het toepassen van de
gegenereerde stylesheet op de QApplication. Gescheiden van ``theme.py``
zodat de pure Python-logica los van Qt getest kan worden.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from app.theme import BASIC_THEME_NAME, Theme, create_basic_theme
from ui.table_styles import configure_from_theme

THEMES_DIR = Path(__file__).resolve().parent.parent / 'themes'
DEFAULT_THEME = 'DKIB'
APP_VENDOR = 'DKIB_geotechniek'
APP_NAME = 'Dsheet_dashboard'


def _gebruikers_cache_dir() -> Path:
    """Geef een gebruikersspecifieke temp-cachemap terug waarin de app mag schrijven.

    De SVG's worden bij elke themabootstrap opnieuw opgebouwd, dus een tempmap
    is voldoende en voorkomt schrijfrechten in de projectmap, Dropbox-map of
    latere installatiemap.
    """
    return Path(tempfile.gettempdir()) / APP_VENDOR / APP_NAME


ICON_CACHE_DIR = _gebruikers_cache_dir() / 'themes' / '_cache'


def bootstrap_theme(actief_thema_naam: str) -> Theme | None:
    """Laad het thema, registreer fonts en pas stylesheet toe op de QApplication.

    Moet worden aangeroepen ná ``QApplication(sys.argv)`` en vóór constructie van
    het hoofdvenster, zodat alle widgets vanaf het begin de juiste styling krijgen.

    Parameters
    ----------
    actief_thema_naam:
        Naam van het thema (bv. 'DKIB'). Verwijst naar ``themes/<naam>.json``
        (case-insensitief gematcht op bestandsnaam).

    Returns
    -------
    Theme | None
        Het geladen thema-object; ``None`` als geen enkel thema geladen kon worden
        (in dat geval blijft de Qt-default stylesheet actief).
    """
    thema = _laad_thema_met_fallback(actief_thema_naam)
    if thema is None:
        return None

    werkelijke_familie = _registreer_fonts(thema.assets.font_files,
                                           fallback=thema.typography.family)
    configure_from_theme(thema)

    qss = thema.build_stylesheet(font_family=werkelijke_familie, icon_dir=ICON_CACHE_DIR)
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(qss)

    return thema


def _laad_thema_met_fallback(naam: str) -> Theme | None:
    """Probeer het gewenste thema te laden; val terug op DKIB; daarna op Basic."""
    if naam.lower() == BASIC_THEME_NAME.lower():
        return create_basic_theme()

    kandidaten = [naam]
    if naam.lower() != DEFAULT_THEME.lower():
        kandidaten.append(DEFAULT_THEME)

    for kandidaat in kandidaten:
        pad = _vind_thema_bestand(kandidaat)
        if pad is None:
            continue
        try:
            return Theme.load(pad)
        except (ValueError, OSError) as exc:
            print(f'Waarschuwing: thema {kandidaat!r} kon niet geladen worden: {exc}',
                  file=sys.stderr)
    return create_basic_theme()


def _vind_thema_bestand(naam: str) -> Path | None:
    """Zoek een themebestand op bestandsnaam of interne theme-naam."""
    if not THEMES_DIR.exists():
        return None
    doel = naam.lower()
    for pad in THEMES_DIR.glob('*.json'):
        if pad.stem.lower() == doel:
            return pad
        try:
            if Theme.load(pad).name.lower() == doel:
                return pad
        except (ValueError, OSError):
            continue
    return None


def _registreer_fonts(font_paden: list[str], fallback: str) -> str:
    """Registreer fonts via QFontDatabase en geef de werkelijke familienaam terug.

    Parameters
    ----------
    font_paden:
        Lijst van absolute paden naar ``.ttf``-bestanden.
    fallback:
        Familienaam om terug te vallen wanneer geen enkele font geladen kon worden.

    Returns
    -------
    str
        De werkelijke font-familienaam zoals door Qt gerapporteerd, of ``fallback``
        wanneer geen enkele font succesvol is geregistreerd.
    """
    werkelijke_naam: str | None = None
    for pad in font_paden:
        font_id = QFontDatabase.addApplicationFont(pad)
        if font_id == -1:
            print(f'Waarschuwing: kon font niet laden: {pad}', file=sys.stderr)
            continue
        if werkelijke_naam is None:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                werkelijke_naam = families[0]

    return werkelijke_naam or fallback
