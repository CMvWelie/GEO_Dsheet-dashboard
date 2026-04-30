"""Zwevend Word-WYSIWYG preview venster voor D-Sheet Dashboard.

Toont een PDF die uit het echte .docx-rapport is gegenereerd, zodat de
gebruiker exact ziet wat in Word terechtkomt — inclusief template-stijlen,
kopjes, tabellen en pagina-indeling.
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QSettings
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)


class WordPdfPreviewWindow(QMainWindow):
    """Zwevend venster dat een PDF-rapportweergave toont in QPdfView."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Word Preview (WYSIWYG)')
        self.resize(820, 1000)
        self._doc = QPdfDocument(self)
        self._build()
        self._herstel_geometrie()

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Statusbalk ────────────────────────────────────────────────
        status_balk = QWidget()
        status_balk.setStyleSheet(
            'background: #f0f4f7; border-bottom: 1px solid #c4d4e0;'
        )
        status_layout = QHBoxLayout(status_balk)
        status_layout.setContentsMargins(10, 4, 10, 4)
        status_layout.setSpacing(0)

        self._status_label = QLabel('Geen rapport geladen')
        self._status_label.setStyleSheet(
            'font-size: 10px; color: #5a7a8a; '
            'font-family: "Segoe UI", sans-serif;'
        )
        self._tijd_label = QLabel('')
        self._tijd_label.setStyleSheet(
            'font-size: 10px; color: #999; font-style: italic; '
            'font-family: "Segoe UI", sans-serif;'
        )

        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        status_layout.addWidget(self._tijd_label)
        layout.addWidget(status_balk)

        # ── PDF-viewer ────────────────────────────────────────────────
        self._view = QPdfView(central)
        self._view.setDocument(self._doc)
        self._view.setPageMode(QPdfView.PageMode.MultiPage)
        self._view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self._view.setStyleSheet('background: #2a2a2a;')
        layout.addWidget(self._view, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_pdf(self, pdf_path: str) -> None:
        """Laad een PDF-bestand in de viewer.

        Parameters
        ----------
        pdf_path:
            Absoluut pad naar het PDF-bestand.
        """
        self._doc.load(pdf_path)
        self._status_label.setStyleSheet(
            'font-size: 10px; color: #2f7d32; '
            'font-family: "Segoe UI", sans-serif;'
        )
        pages = self._doc.pageCount()
        self._status_label.setText(
            f'{pages} pagina geladen' if pages == 1 else f'{pages} pagina\'s geladen'
        )
        self._tijd_label.setText(
            f'↻ Bijgewerkt: {datetime.now().strftime("%H:%M:%S")}'
        )

    def set_status(self, text: str, ok: bool = True) -> None:
        """Toon een statusbericht in de balk."""
        kleur = '#2f7d32' if ok else '#b42318'
        self._status_label.setStyleSheet(
            f'font-size: 10px; color: {kleur}; '
            f'font-family: "Segoe UI", sans-serif;'
        )
        self._status_label.setText(text)

    def set_busy(self, busy: bool) -> None:
        """Toon dat er een conversie loopt."""
        if busy:
            self._status_label.setStyleSheet(
                'font-size: 10px; color: #5a7a8a; '
                'font-family: "Segoe UI", sans-serif;'
            )
            self._status_label.setText('Bezig met genereren…')
            self._tijd_label.setText('')

    # ------------------------------------------------------------------
    # Geometrie-persistentie
    # ------------------------------------------------------------------

    def _herstel_geometrie(self) -> None:
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        geom = instellingen.value('word_pdf_preview_window/geometry')
        if geom:
            self.restoreGeometry(geom)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        instellingen.setValue(
            'word_pdf_preview_window/geometry', self.saveGeometry()
        )
        super().closeEvent(event)
