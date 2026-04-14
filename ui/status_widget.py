"""Gekleurde statusbadge voor D-Sheet Dashboard."""

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class StatusWidget(QWidget):
    """Gekleurde statusbadge + tekstregel."""

    _STYLES = {
        'ok':   ('color:#2f7d32;background:#eef8ef;border:1px solid #9ac89c;', '✔ '),
        'warn': ('color:#b26a00;background:#fff7eb;border:1px solid #e2be83;', '⚠ '),
        'err':  ('color:#b42318;background:#fff2f1;border:1px solid #e5a6a1;', '✖ '),
        'idle': ('color:#555555;background:#f4f4f4;border:1px solid #cccccc;', '· '),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._badge = QLabel('Gereed')
        self._badge.setStyleSheet(
            'border-radius:8px;padding:4px 8px;font-size:12px;font-weight:bold;'
        )
        self._detail = QLabel('')
        self._detail.setStyleSheet('color:#5f6b76;font-size:11px;')
        self._detail.setWordWrap(True)
        layout.addWidget(self._badge)
        layout.addWidget(self._detail)
        self.set_status('idle', 'Gereed', 'Importeer bestanden om te beginnen.')

    def set_status(self, kind: str, text: str, detail: str = '') -> None:
        style, prefix = self._STYLES.get(kind, self._STYLES['idle'])
        self._badge.setStyleSheet(
            f'{style}border-radius:8px;padding:4px 8px;'
            f'font-size:12px;font-weight:bold;'
        )
        self._badge.setText(prefix + text)
        self._detail.setText(detail)
