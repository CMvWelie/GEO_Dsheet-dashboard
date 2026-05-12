"""Persistente eenmalige sessie-overdracht bij applicatie-herstart.

Wordt gebruikt door de 'Applicatie herstarten'-knop in Tab Instellingen om
de huidig ingeladen bestandspaden door te geven aan de nieuwe Python-instantie,
zodat de gebruiker na herstart dezelfde projecten geladen vindt.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config_manager import CONFIG_DIR

SESSION_FILE: Path = CONFIG_DIR / 'restart_session.json'


def save(paths: list[str]) -> None:
    """Sla een lijst paden op voor de eerstvolgende app-start.

    Parameters
    ----------
    paths:
        Absolute paden naar ``.shd``-bestanden.
        Een lege lijst schrijft niets.
    """
    if not paths:
        return
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(
        json.dumps({'paths': list(paths)}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def pop() -> list[str]:
    """Lees en verwijder het sessiebestand. Geeft de paden terug, of een lege lijst.

    Wordt eenmalig aangeroepen bij app-start; het bestand wordt direct
    verwijderd zodat een crash of bug geen oneindige herlaad-loop veroorzaakt.
    """
    if not SESSION_FILE.exists():
        return []
    try:
        data = json.loads(SESSION_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        _verwijder_stil()
        return []
    _verwijder_stil()
    paden = data.get('paths', [])
    if not isinstance(paden, list):
        return []
    return [p for p in paden if isinstance(p, str)]


def _verwijder_stil() -> None:
    try:
        SESSION_FILE.unlink()
    except OSError:
        pass
