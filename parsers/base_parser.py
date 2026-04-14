"""Gedeelde hulpfuncties voor D-Sheet parsers."""

from __future__ import annotations
import re


def extract_section(text: str, section_name: str) -> str:
    """Extraheer de inhoud tussen [SECTION] en [END OF SECTION] tags.

    Parameters
    ----------
    text:         Volledige bestandstekst.
    section_name: Naam van de sectie (zonder haakjes).

    Returns
    -------
    str  Inhoud van de sectie, of lege string als niet gevonden.
    """
    safe = re.escape(section_name)
    pattern = rf'\[{safe}\]([\s\S]*?)\[END OF {safe}\]'
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else ''


def find_line_value(text: str, pattern: re.Pattern | str) -> str:
    """Zoek de eerste capture-groep van een regex-patroon in tekst.

    Parameters
    ----------
    text:    Tekst om in te zoeken.
    pattern: Reguliere expressie met minimaal één capture-groep.

    Returns
    -------
    str  Gevonden waarde (getrimmd), of lege string.
    """
    m = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else ''
