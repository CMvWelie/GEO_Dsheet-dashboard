"""Qt-aware bootstrap voor het thema-systeem.

Verantwoordelijk voor het registreren van fonts en het toepassen van de
gegenereerde stylesheet op de QApplication. Gescheiden van ``theme.py``
zodat de pure Python-logica los van Qt getest kan worden.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from app.theme import Theme

THEMES_DIR = Path(__file__).resolve().parent.parent / 'themes'
DEFAULT_THEME = 'DKIB'


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
                                           fallback=thema.typography.fallback)

    qss = thema.build_stylesheet(font_family=werkelijke_familie)
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(qss)

    return thema


def _laad_thema_met_fallback(naam: str) -> Theme | None:
    """Probeer het gewenste thema te laden; val terug op DKIB; daarna op niets."""
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
    return None


def _vind_thema_bestand(naam: str) -> Path | None:
    """Zoek ``<themes_dir>/<naam>.json`` (case-insensitief)."""
    if not THEMES_DIR.exists():
        return None
    doel = naam.lower()
    for pad in THEMES_DIR.glob('*.json'):
        if pad.stem.lower() == doel:
            return pad
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
