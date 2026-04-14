"""Zwevend Word-preview venster voor D-Sheet Dashboard."""

from __future__ import annotations
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
)
from PyQt6.QtCore import QSettings


class WordPreviewWindow(QMainWindow):
    """Zwevend venster dat een HTML-rapportweergave toont in QTextBrowser.

    Het venster is bewust 'dom': het ontvangt alleen een HTML-string via
    set_html() en heeft geen directe toegang tot AppState of controllers.
    Positie en grootte worden onthouden via QSettings.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Word Preview')
        self.resize(720, 900)
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

        self._count_label = QLabel('Geen secties')
        self._count_label.setStyleSheet(
            'font-size: 10px; color: #5a7a8a; '
            'font-family: "Segoe UI", sans-serif;'
        )
        self._tijd_label = QLabel('')
        self._tijd_label.setStyleSheet(
            'font-size: 10px; color: #999; font-style: italic; '
            'font-family: "Segoe UI", sans-serif;'
        )

        status_layout.addWidget(self._count_label)
        status_layout.addStretch()
        status_layout.addWidget(self._tijd_label)
        layout.addWidget(status_balk)

        # ── Preview-browser ───────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.setStyleSheet('border: none; background: white;')
        layout.addWidget(self._browser, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def set_html(self, html: str, sectie_count: int = 0) -> None:
        """Toon nieuwe HTML-inhoud en werk de statusbalk bij.

        Parameters
        ----------
        html:
            Volledige HTML-string voor QTextBrowser.setHtml().
        sectie_count:
            Aantal geselecteerde secties voor de statusregel.
        """
        self._browser.setHtml(html)
        enkelvoud = sectie_count == 1
        self._count_label.setText(
            f'{sectie_count} sectie geselecteerd'
            if enkelvoud else
            f'{sectie_count} secties geselecteerd'
        )
        self._tijd_label.setText(
            f'↻ Bijgewerkt: {datetime.now().strftime("%H:%M")}'
        )

    # ------------------------------------------------------------------
    # Geometrie-persistentie
    # ------------------------------------------------------------------

    def _herstel_geometrie(self) -> None:
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        geom = instellingen.value('preview_window/geometry')
        if geom:
            self.restoreGeometry(geom)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        instellingen = QSettings('DKIB', 'DSheetDashboard')
        instellingen.setValue('preview_window/geometry', self.saveGeometry())
        super().closeEvent(event)
