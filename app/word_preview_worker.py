"""WordPreviewWorker — QThread-worker voor Word→PDF preview."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from app.docx_to_pdf_converter import DocxToPdfConverter
from app.report_controller import ReportController


class WordPreviewWorker(QObject):
    """Genereert .docx via ReportController en converteert naar .pdf.

    Werkt op een aparte QThread; de UI-thread blijft responsief.
    Communiceert via signalen — geen directe UI-interactie.
    """

    finished = pyqtSignal(str)
    """Pad naar succesvol aangemaakte PDF."""
    failed = pyqtSignal(str)
    """Foutmelding bij mislukken (export of conversie)."""

    def __init__(self,
                 controller: ReportController,
                 converter: DocxToPdfConverter,
                 parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._converter = converter

    @pyqtSlot()
    def run(self) -> None:
        """Voer export en conversie uit (aanroepen via QThread.started)."""
        tmpdir = tempfile.mkdtemp(prefix='dsheet_preview_')
        docx_path = os.path.join(tmpdir, 'preview.docx')
        pdf_path = os.path.join(tmpdir, 'preview.pdf')

        export_fout = self._controller.export_word(docx_path)
        if export_fout is not None:
            self.failed.emit(f'Word-export mislukte: {export_fout}')
            return
        if not Path(docx_path).exists():
            self.failed.emit('Word-export gaf geen bestand')
            return

        conv_fout = self._converter.convert(docx_path, pdf_path)
        if conv_fout is not None:
            self.failed.emit(f'PDF-conversie mislukte: {conv_fout}')
            return

        self.finished.emit(pdf_path)
