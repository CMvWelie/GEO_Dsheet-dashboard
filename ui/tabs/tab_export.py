"""Tab Export — PNG, Excel en Word export in sub-tabbladen."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QTabWidget,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal

from ui.tabs.tab_excel_export import TabExcelExport
from ui.tabs.tab_word_export import TabWordExport


class _TabPng(QWidget):
    """Eenvoudig PNG-exportpaneel."""

    export_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        box = QGroupBox('PNG-export')
        bvl = QVBoxLayout(box)
        info = QLabel(
            'Exporteert de actieve doorsnede-weergave als PNG-afbeelding.\n'
            'U kiest de opslaglocatie in het volgende venster.'
        )
        info.setWordWrap(True)
        info.setObjectName('hintLabel')
        bvl.addWidget(info)

        btn = QPushButton('Exporteer als PNG…')
        btn.setObjectName('btnPrimary')
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(self.export_requested)
        bvl.addWidget(btn)

        self._status = QLabel('')
        self._status.setWordWrap(True)
        bvl.addWidget(self._status)

        root.addWidget(box)
        root.addStretch()

    def set_status(self, text: str, ok: bool = True) -> None:
        color = '#2f7d32' if ok else '#b42318'
        self._status.setStyleSheet(f'color:{color};font-size:11px;')
        self._status.setText(text)


class TabExport(QWidget):
    """Exporttab met sub-tabs voor PNG, Excel en Word."""

    # Doorsturen van signalen van de sub-tabs
    export_png_requested = pyqtSignal()
    export_excel_requested = pyqtSignal(str)   # output_path
    export_word_requested = pyqtSignal(str)    # output_path
    excel_template_changed = pyqtSignal(str)
    word_template_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._sub_tabs = QTabWidget()
        self._sub_tabs.setDocumentMode(True)

        self._png_tab = _TabPng()
        self._sub_tabs.addTab(self._png_tab, 'PNG')

        self.excel_tab = TabExcelExport()
        self._sub_tabs.addTab(self.excel_tab, 'Excel')

        self.word_tab = TabWordExport()
        self._sub_tabs.addTab(self.word_tab, 'Word')

        root.addWidget(self._sub_tabs)

        # Signalen doorsturen
        self._png_tab.export_requested.connect(self.export_png_requested)
        self.excel_tab.export_requested.connect(self.export_excel_requested)
        self.excel_tab.template_changed.connect(self.excel_template_changed)
        self.word_tab.export_requested.connect(self.export_word_requested)
        self.word_tab.template_changed.connect(self.word_template_changed)

    def set_png_status(self, text: str, ok: bool = True) -> None:
        self._png_tab.set_status(text, ok)
