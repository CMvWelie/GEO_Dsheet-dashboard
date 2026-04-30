# Word WYSIWYG Preview — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Naast de bestaande snelle HTML-preview een tweede preview-knop "Word preview (WYSIWYG)" toevoegen die het echte `.docx` genereert via `WordExporter`, dat naar PDF converteert (Word COM via `docx2pdf`, met LibreOffice-fallback) en in een apart venster met `QPdfView` toont — zodat de gebruiker exact ziet wat in Word terechtkomt, inclusief template-stijlen.

**Architecture:** Pure additie op de bestaande rapportagepijplijn. Een nieuwe service `DocxToPdfConverter` detecteert beschikbare conversie-engines en doet de conversie. Een `WordPreviewWorker` (QObject op een aparte `QThread`) draait `ReportController.export_word()` naar een tempfile en de PDF-conversie zonder de UI-thread te blokkeren. Een nieuw `WordPdfPreviewWindow` (QMainWindow met `QPdfView`) toont het resultaat. De bestaande `HtmlPreviewBuilder` + `WordPreviewWindow` blijft volledig ongewijzigd.

**Tech Stack:** PyQt6 (`QThread`, `QtPdfWidgets.QPdfView`, `QtPdf.QPdfDocument`), `python-docx` (al aanwezig), `docx2pdf` (nieuw, optioneel — Word COM op Windows), LibreOffice `soffice --headless --convert-to pdf` (subprocess, optioneel).

---

## Bestandsstructuur

**Nieuwe bestanden:**
- `app/docx_to_pdf_converter.py` — engine-detectie en conversie (geen Qt)
- `app/word_preview_worker.py` — `QObject`-worker voor `QThread` (Qt, maar geen widgets)
- `ui/word_pdf_preview_window.py` — `QMainWindow` met `QPdfView`
- `tests/test_docx_to_pdf_converter.py` — engine-detectie en pad-validatie

**Te wijzigen bestanden:**
- `requirements.txt` — voeg `docx2pdf>=0.1.8` toe
- `ui/tabs/tab_report_select.py` — extra knop + signaal `word_pdf_preview_open_requested`
- `app/main_window.py` — instantiëren venster + worker, wiring, slot

**Niet aanraken:**
- `reporting/builders/html_preview_builder.py` (blijft de snelle preview)
- `ui/preview_window.py` (blijft de HTML-preview-window)
- `exporters/word_exporter.py` (wordt as-is hergebruikt)
- `app/report_controller.py` (`export_word()` voldoet)

---

## Task 1: Dependency toevoegen

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Voeg `docx2pdf` toe**

`requirements.txt` wordt:

```
PyQt6>=6.4.0
matplotlib>=3.7.0
numpy>=1.24.0
openpyxl>=3.1.0
python-docx>=1.0.0
docx2pdf>=0.1.8
```

- [ ] **Step 2: Installeer**

Run: `pip install -r requirements.txt`
Expected: `Successfully installed docx2pdf-0.1.x`

- [ ] **Step 3: Verifieer import**

Run: `python -c "import docx2pdf; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: voeg docx2pdf toe voor Word WYSIWYG preview"
```

---

## Task 2: DocxToPdfConverter — engine-detectie

**Files:**
- Create: `app/docx_to_pdf_converter.py`
- Test: `tests/test_docx_to_pdf_converter.py`

**Verantwoordelijkheid:** Detecteer welke conversie-engines beschikbaar zijn op het systeem. Geen daadwerkelijke conversie nog; dat komt in Task 3.

- [ ] **Step 1: Schrijf de tests**

Maak `tests/test_docx_to_pdf_converter.py`:

```python
"""Tests voor DocxToPdfConverter."""

from __future__ import annotations
from unittest.mock import patch

from app.docx_to_pdf_converter import DocxToPdfConverter


def test_no_engines_when_nothing_available():
    """Als geen engine beschikbaar is, is available_engines leeg."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=False), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        assert conv.available_engines() == []
        assert conv.is_available() is False


def test_docx2pdf_detected():
    """Als docx2pdf importeerbaar is, staat 'docx2pdf' in lijst."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=True), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        assert 'docx2pdf' in conv.available_engines()
        assert conv.is_available() is True


def test_libreoffice_detected():
    """Als soffice gevonden wordt, staat 'libreoffice' in lijst."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=False), \
         patch('app.docx_to_pdf_converter._find_libreoffice',
                return_value=r'C:\Program Files\LibreOffice\program\soffice.exe'):
        conv = DocxToPdfConverter()
        assert 'libreoffice' in conv.available_engines()
        assert conv.is_available() is True


def test_preferred_order_docx2pdf_first():
    """Als beide beschikbaar zijn, staat docx2pdf vooraan (Windows-default)."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=True), \
         patch('app.docx_to_pdf_converter._find_libreoffice',
                return_value='/usr/bin/soffice'):
        conv = DocxToPdfConverter()
        assert conv.available_engines() == ['docx2pdf', 'libreoffice']
```

- [ ] **Step 2: Run de tests om falen te bevestigen**

Run: `pytest tests/test_docx_to_pdf_converter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.docx_to_pdf_converter'`

- [ ] **Step 3: Schrijf `app/docx_to_pdf_converter.py`**

```python
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
```

- [ ] **Step 4: Run de tests opnieuw**

Run: `pytest tests/test_docx_to_pdf_converter.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/docx_to_pdf_converter.py tests/test_docx_to_pdf_converter.py
git commit -m "feat: DocxToPdfConverter met engine-detectie (docx2pdf + LibreOffice)"
```

---

## Task 3: DocxToPdfConverter — daadwerkelijke conversie

**Files:**
- Modify: `app/docx_to_pdf_converter.py`
- Modify: `tests/test_docx_to_pdf_converter.py`

**Verantwoordelijkheid:** Methode `convert(docx_path, pdf_path) -> str | None` die de eerste beschikbare engine gebruikt. Foutafhandeling via teruggegeven foutmelding (consistent met `WordExporter.export()`).

- [ ] **Step 1: Voeg test toe voor pad-validatie**

Voeg onderaan `tests/test_docx_to_pdf_converter.py` toe:

```python
def test_convert_returns_error_when_no_engines(tmp_path):
    """Zonder engine geeft convert een leesbare fout terug."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=False), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        docx = tmp_path / 'in.docx'
        docx.write_bytes(b'fake')
        fout = conv.convert(str(docx), str(tmp_path / 'out.pdf'))
        assert fout is not None
        assert 'engine' in fout.lower()


def test_convert_returns_error_when_input_missing(tmp_path):
    """Als invoerbestand niet bestaat, krijg je een leesbare fout."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=True), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        fout = conv.convert(str(tmp_path / 'bestaatniet.docx'),
                              str(tmp_path / 'out.pdf'))
        assert fout is not None
        assert 'bestaat niet' in fout.lower() or 'niet gevonden' in fout.lower()
```

- [ ] **Step 2: Run de nieuwe tests om falen te bevestigen**

Run: `pytest tests/test_docx_to_pdf_converter.py -v`
Expected: 2 nieuwe tests FAIL — `AttributeError: 'DocxToPdfConverter' object has no attribute 'convert'`

- [ ] **Step 3: Voeg `convert()` toe aan `app/docx_to_pdf_converter.py`**

Voeg onderaan de klasse toe:

```python
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
        """Converteer via docx2pdf (Word COM op Windows)."""
        import docx2pdf  # type: ignore[import-untyped]
        docx2pdf.convert(docx_path, pdf_path)

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
```

- [ ] **Step 4: Run alle tests opnieuw**

Run: `pytest tests/test_docx_to_pdf_converter.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/docx_to_pdf_converter.py tests/test_docx_to_pdf_converter.py
git commit -m "feat: DocxToPdfConverter.convert() met docx2pdf + LibreOffice fallback"
```

---

## Task 4: WordPreviewWorker — async export + conversie

**Files:**
- Create: `app/word_preview_worker.py`

**Verantwoordelijkheid:** Een `QObject`-worker die op een `QThread` draait. Wordt aangeroepen met een `ReportController` en een output-pad. Roept `controller.export_word()` aan, dan `converter.convert()`, en emit signalen `finished(pdf_path)` of `failed(message)`.

Geen tests — dit is een dunne Qt-glue laag; getest via integratie/handmatig in Task 7.

- [ ] **Step 1: Schrijf het bestand**

Maak `app/word_preview_worker.py`:

```python
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
```

- [ ] **Step 2: Verifieer import**

Run: `python -c "from app.word_preview_worker import WordPreviewWorker; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/word_preview_worker.py
git commit -m "feat: WordPreviewWorker — QThread-worker voor docx→pdf preview"
```

---

## Task 5: WordPdfPreviewWindow — PDF-viewer

**Files:**
- Create: `ui/word_pdf_preview_window.py`

**Verantwoordelijkheid:** `QMainWindow` met `QPdfView`. Net als `WordPreviewWindow`: dom — alleen `set_pdf(path)`, `set_status(text, ok)`, `set_busy(busy)`. Eigen `QSettings`-key voor geometriepersistentie.

- [ ] **Step 1: Schrijf het bestand**

Maak `ui/word_pdf_preview_window.py`:

```python
"""Zwevend Word-WYSIWYG preview venster voor D-Sheet Dashboard.

Toont een PDF die uit het echte .docx-rapport is gegenereerd, zodat de
gebruiker exact ziet wat in Word terechtkomt — inclusief template-stijlen,
kopjes, tabellen en pagina-indeling.
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QSettings, QUrl
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
        self._view = QPdfView()
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
```

- [ ] **Step 2: Verifieer import**

Run: `python -c "from ui.word_pdf_preview_window import WordPdfPreviewWindow; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add ui/word_pdf_preview_window.py
git commit -m "feat: WordPdfPreviewWindow met QPdfView voor WYSIWYG preview"
```

---

## Task 6: Knop + signaal in TabReportSelect

**Files:**
- Modify: `ui/tabs/tab_report_select.py`

**Verantwoordelijkheid:** Naast de bestaande "↗ Preview openen"-knop een tweede knop toevoegen: "📄 Word preview (WYSIWYG)". Nieuw signaal `word_pdf_preview_open_requested`. Helper `set_word_pdf_preview_enabled(beschikbaar, tooltip)` om de knop te disablen als geen engine aanwezig is.

- [ ] **Step 1: Voeg het signaal toe**

In `ui/tabs/tab_report_select.py` direct na `preview_open_requested` (rond regel 18):

```python
    word_pdf_preview_open_requested = pyqtSignal()
    """Afgegeven als de gebruiker op 'Word preview (WYSIWYG)' klikt."""
```

- [ ] **Step 2: Voeg de tweede knop toe in `_build()`**

Vervang het blok `# ── Preview-venster ──` (rond regel 94–104) door:

```python
        # ── Preview-vensters ──────────────────────────────────────────
        prev_rij = QHBoxLayout()
        open_btn = QPushButton('↗ Preview openen')
        open_btn.setObjectName('btnPrimary')
        open_btn.clicked.connect(self.preview_open_requested)
        prev_hint = QLabel('Snelle HTML-preview naast de applicatie')
        prev_hint.setObjectName('hintLabel')
        prev_rij.addWidget(open_btn)
        prev_rij.addWidget(prev_hint)
        prev_rij.addStretch()
        root.addLayout(prev_rij)

        wysiwyg_rij = QHBoxLayout()
        self._word_preview_btn = QPushButton('📄 Word preview (WYSIWYG)')
        self._word_preview_btn.setObjectName('btnPrimary')
        self._word_preview_btn.clicked.connect(
            self.word_pdf_preview_open_requested
        )
        wysiwyg_hint = QLabel(
            'Genereert het echte .docx en toont als PDF — exact zoals in Word'
        )
        wysiwyg_hint.setObjectName('hintLabel')
        wysiwyg_rij.addWidget(self._word_preview_btn)
        wysiwyg_rij.addWidget(wysiwyg_hint)
        wysiwyg_rij.addStretch()
        root.addLayout(wysiwyg_rij)
```

- [ ] **Step 3: Voeg helper toe onder "Publieke interface"**

Voeg na `set_word_status(...)` toe:

```python
    def set_word_pdf_preview_enabled(self, beschikbaar: bool,
                                       tooltip: str = '') -> None:
        """Schakel de WYSIWYG-knop in/uit op basis van engine-beschikbaarheid.

        Parameters
        ----------
        beschikbaar:
            True als minstens één conversie-engine beschikbaar is.
        tooltip:
            Hint die bij hover getoond wordt (bijv. installatie-instructie).
        """
        self._word_preview_btn.setEnabled(beschikbaar)
        self._word_preview_btn.setToolTip(tooltip)
```

- [ ] **Step 4: Smoke-test de tab**

Run: `python -c "from ui.tabs.tab_report_select import TabReportSelect; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add ui/tabs/tab_report_select.py
git commit -m "feat: tweede preview-knop voor Word WYSIWYG in rapportagetab"
```

---

## Task 7: Bedrading in MainWindow

**Files:**
- Modify: `app/main_window.py`

**Verantwoordelijkheid:** `WordPdfPreviewWindow` instantiëren, `DocxToPdfConverter` aanmaken, knop disablen als geen engine, slot `_on_word_pdf_preview_open()` die de worker op een `QThread` start, signalen routeren naar het venster, en bij `selection_changed` het venster herrenderen als het zichtbaar is.

- [ ] **Step 1: Imports toevoegen**

Bovenaan `app/main_window.py`, na de bestaande `from ui.preview_window import WordPreviewWindow`:

```python
from ui.preview_window import WordPreviewWindow
from ui.word_pdf_preview_window import WordPdfPreviewWindow
from app.docx_to_pdf_converter import DocxToPdfConverter
from app.word_preview_worker import WordPreviewWorker
from PyQt6.QtCore import QThread
```

(Als `QThread` al via een andere import in dat bestand staat, voeg het dan niet dubbel toe.)

- [ ] **Step 2: Instantiëren in `__init__()`**

Direct na `self._preview_window = WordPreviewWindow()` (rond regel 96):

```python
        self._preview_window = WordPreviewWindow()
        self._html_builder = HtmlPreviewBuilder()

        self._word_pdf_preview_window = WordPdfPreviewWindow()
        self._docx_to_pdf = DocxToPdfConverter()
        self._word_preview_thread: QThread | None = None
        self._word_preview_worker: WordPreviewWorker | None = None
```

- [ ] **Step 3: Knop-status zetten direct na `_build_ui()`**

Voeg direct na `self._build_ui()` (vóór `self._connect_signals()`) toe:

```python
        if self._docx_to_pdf.is_available():
            engines = ', '.join(self._docx_to_pdf.available_engines())
            self._tab_report_select.set_word_pdf_preview_enabled(
                True, f'Beschikbare engines: {engines}'
            )
        else:
            self._tab_report_select.set_word_pdf_preview_enabled(
                False,
                'Geen Word/LibreOffice gevonden — installeer Microsoft Word '
                'of LibreOffice om deze preview te gebruiken.'
            )
```

- [ ] **Step 4: Signal-wiring in `_connect_signals()`**

Voeg na `self._tab_report_select.selection_changed.connect(self._update_preview)` (rond regel 332) toe:

```python
        self._tab_report_select.word_pdf_preview_open_requested.connect(
            self._on_word_pdf_preview_open
        )
        self._tab_report_select.selection_changed.connect(
            self._update_word_pdf_preview
        )
```

- [ ] **Step 5: Slots toevoegen**

Direct onder `_update_preview()` (rond regel 961) toevoegen:

```python
    def _on_word_pdf_preview_open(self) -> None:
        """Open het Word-WYSIWYG preview-venster en start een conversie."""
        self._word_pdf_preview_window.show()
        self._word_pdf_preview_window.raise_()
        self._start_word_pdf_conversie()

    def _update_word_pdf_preview(self) -> None:
        """Herrender de Word-WYSIWYG preview als het venster zichtbaar is."""
        if not self._word_pdf_preview_window.isVisible():
            return
        self._start_word_pdf_conversie()

    def _start_word_pdf_conversie(self) -> None:
        """Start een nieuwe export+conversie op een aparte thread.

        Een lopende conversie wordt niet onderbroken; de gebruiker moet
        wachten tot die klaar is voordat een nieuwe start.
        """
        if not self._docx_to_pdf.is_available():
            self._word_pdf_preview_window.set_status(
                'Geen conversie-engine beschikbaar', ok=False
            )
            return
        if self._word_preview_thread is not None and \
                self._word_preview_thread.isRunning():
            return  # negeer; lopende conversie eerst afmaken

        self._word_pdf_preview_window.set_busy(True)

        thread = QThread(self)
        worker = WordPreviewWorker(self._report_controller, self._docx_to_pdf)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_word_pdf_finished)
        worker.failed.connect(self._on_word_pdf_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_word_pdf_thread_finished)

        self._word_preview_thread = thread
        self._word_preview_worker = worker
        thread.start()

    def _on_word_pdf_finished(self, pdf_path: str) -> None:
        """Toon het PDF-resultaat in het preview-venster."""
        self._word_pdf_preview_window.set_pdf(pdf_path)

    def _on_word_pdf_failed(self, message: str) -> None:
        """Toon een foutmelding in het preview-venster."""
        self._word_pdf_preview_window.set_status(message, ok=False)

    def _on_word_pdf_thread_finished(self) -> None:
        """Reset thread-referenties zodat een volgende conversie kan starten."""
        self._word_preview_thread = None
        self._word_preview_worker = None
```

- [ ] **Step 6: Smoke-test imports**

Run: `python -c "from app.main_window import MainWindow; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add app/main_window.py
git commit -m "feat: bedraad Word WYSIWYG preview in MainWindow met QThread-worker"
```

---

## Task 8: Handmatige rooktest

Geen automatische tests voor deze laag — de keten Word-COM/LibreOffice is omgevingsafhankelijk en moet door een mens worden geverifieerd.

- [ ] **Step 1: Start de app**

Run: `python run.pyw`
Expected: app start zonder errors

- [ ] **Step 2: Laad een testproject**

Importeer een `.shi`/`.shd`/`.shs` bundel en klik "Verwerk".
Expected: project verschijnt in dropdown.

- [ ] **Step 3: Open de Rapportage-tab → "Selectie" subtab**

Expected: twee preview-knoppen zichtbaar:
- "↗ Preview openen" (HTML — bestaand)
- "📄 Word preview (WYSIWYG)" (nieuw)

- [ ] **Step 4: Test HTML-preview (regressie)**

Klik "↗ Preview openen".
Expected: bestaande HTML-preview opent en toont secties zoals voorheen.

- [ ] **Step 5: Test WYSIWYG-preview**

Klik "📄 Word preview (WYSIWYG)".
Expected:
- Statusbalk toont "Bezig met genereren…"
- UI blijft responsief (sleep het venster om dit te testen)
- Na 1–4 seconden verschijnt de PDF, statusbalk toont "N pagina's geladen"
- De PDF gebruikt de stijlen uit `templates/damwand_stijlen.docx` (of geen template als er geen is geselecteerd)

- [ ] **Step 6: Test live-update**

Met het WYSIWYG-venster open: vink in de Rapportage-tab een item uit/aan.
Expected: na enkele seconden ververst de PDF automatisch.

- [ ] **Step 7: Test fout-pad — disable Word**

Stop alle Word-processen, hernoem (tijdelijk) de docx2pdf-installatie of test op een machine zonder Word/LibreOffice.
Expected: de WYSIWYG-knop is uitgeschakeld; tooltip vermeldt installatie-vereiste.

- [ ] **Step 8: Test geometrie-persistentie**

Verplaats en hervorm het WYSIWYG-venster, sluit het, heropen het.
Expected: positie en grootte zijn hersteld.

- [ ] **Step 9: Commit (geen code, maar markeer gereed)**

Geen extra commit nodig; bij succes is de feature compleet.

---

## Self-review notities

**Spec coverage:**
- Twee knoppen naast elkaar ✓ (Task 6)
- Bestaande HTML-preview blijft ongewijzigd ✓ (`HtmlPreviewBuilder`/`WordPreviewWindow` niet aangeraakt)
- Echte `.docx` via bestaande `WordExporter` ✓ (`ReportController.export_word()` in worker)
- Conversie naar PDF met fallback ✓ (`DocxToPdfConverter` met docx2pdf + LibreOffice)
- Threading → UI niet bevriezen ✓ (`QThread` in Task 7)
- Knop disablen als geen engine ✓ (Task 7 Step 3)
- Aparte `QSettings`-key ✓ (`word_pdf_preview_window/geometry`)
- Live-update bij `selection_changed` ✓ (Task 7 Step 4)

**Bekende beperkingen (bewust niet in plan):**
- Geen debounce op `selection_changed` — als de gebruiker snel klikt en een conversie loopt, wordt de volgende klik genegeerd (`isRunning()`-check). Voldoende voor v1; debounce kan in een volgende iteratie.
- Tempfiles worden niet expliciet opgeruimd — Windows ruimt `%TEMP%` periodiek op. Acceptabel voor v1.
- Geen progress-balk; alleen statusbalk-tekst. Voldoende voor 1–4 sec conversies.
- `docx2pdf` op Windows opent een onzichtbare Word-instantie; als de gebruiker het te previewen .docx óók in Word open heeft staan kan een file-lock optreden. Wordt zichtbaar als foutmelding in de statusbalk.
