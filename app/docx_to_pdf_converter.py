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

    # ------------------------------------------------------------------
    # Conversie
    # ------------------------------------------------------------------

    def convert(self, docx_path: str, pdf_path: str) -> str | None:
        """Converteer .docx naar .pdf met de eerste beschikbare engine.

        Parameters
        ----------
        docx_path:
            Pad naar het bron-.docx-bestand.
        pdf_path:
            Pad waar het PDF-bestand wordt opgeslagen.

        Returns
        -------
        str | None
            None bij succes, foutmelding bij een fout.
        """
        if not Path(docx_path).exists():
            return f'Bron-bestand bestaat niet: {docx_path}'
        if not self._engines:
            return ('Geen conversie-engine beschikbaar. '
                    'Installeer Microsoft Word of LibreOffice.')

        laatste_fout: str | None = None
        for engine in self._engines:
            try:
                if engine == 'docx2pdf':
                    self._convert_docx2pdf(docx_path, pdf_path)
                elif engine == 'libreoffice':
                    self._convert_libreoffice(docx_path, pdf_path)
                if Path(pdf_path).exists():
                    return None
                laatste_fout = f'{engine}: PDF niet aangemaakt'
            except Exception as exc:
                laatste_fout = f'{engine}: {exc}'
        return laatste_fout or 'Conversie mislukt zonder details'

    def _convert_docx2pdf(self, docx_path: str, pdf_path: str) -> None:
        """Converteer via docx2pdf (Word COM op Windows).

        docx2pdf gebruikt intern tqdm voor een voortgangsbalk; onder
        ``pythonw.exe`` (GUI-context) is ``sys.stdout`` echter ``None``,
        waardoor tqdm met ``AttributeError: 'NoneType' object has no
        attribute 'write'`` crasht. We zetten daarom tijdelijk een
        dummy-stream zodat de conversie netjes verloopt.
        """
        import io
        import sys
        import docx2pdf  # type: ignore[import-untyped]
        bewaard_stdout, bewaard_stderr = sys.stdout, sys.stderr
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()
        try:
            docx2pdf.convert(docx_path, pdf_path)
        finally:
            sys.stdout = bewaard_stdout
            sys.stderr = bewaard_stderr

    def _convert_libreoffice(self, docx_path: str, pdf_path: str) -> None:
        """Converteer via `soffice --headless --convert-to pdf`."""
        soffice = _find_libreoffice()
        if soffice is None:
            raise RuntimeError('soffice niet gevonden')
        uitvoer_dir = str(Path(pdf_path).parent)
        result = subprocess.run(
            [soffice, '--headless', '--convert-to', 'pdf',
             '--outdir', uitvoer_dir, docx_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or 'soffice faalde')
        # soffice schrijft naar <stem>.pdf in outdir; hernoem naar gevraagd pad
        verwacht = Path(uitvoer_dir) / (Path(docx_path).stem + '.pdf')
        if verwacht != Path(pdf_path) and verwacht.exists():
            verwacht.replace(pdf_path)
