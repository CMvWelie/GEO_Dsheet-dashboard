"""DocxToPdfConverter — converteert .docx naar .pdf via Word COM of LibreOffice."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _has_docx2pdf() -> bool:
    """Geef True als docx2pdf importeerbaar is (Windows + Word vereist runtime)."""
    try:
        import docx2pdf  # noqa: F401
        return True
    except Exception:
        return False


def _find_libreoffice() -> str | None:
    """Zoek het soffice-uitvoerbestand op gangbare locaties."""
    # 1. PATH
    for naam in ('soffice', 'libreoffice'):
        gevonden = shutil.which(naam)
        if gevonden:
            return gevonden
    # 2. Standaard Windows-installatiepaden
    kandidaten = [
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
    ]
    for pad in kandidaten:
        if os.path.exists(pad):
            return pad
    return None


class DocxToPdfConverter:
    """Detecteert beschikbare engines en converteert .docx naar .pdf.

    Engine-prioriteit (Windows): docx2pdf > LibreOffice headless.
    Op andere platformen valt docx2pdf weg en gebruiken we LibreOffice.
    """

    def __init__(self) -> None:
        engines: list[str] = []
        if _has_docx2pdf():
            engines.append('docx2pdf')
        if _find_libreoffice() is not None:
            engines.append('libreoffice')
        self._engines = engines

    def available_engines(self) -> list[str]:
        """Geef lijst van engines die op dit systeem werken."""
        return list(self._engines)

    def is_available(self) -> bool:
        """Geef True als minstens één engine beschikbaar is."""
        return bool(self._engines)
