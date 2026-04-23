"""Session-scoped QApplication voor PyQt6 widget-tests."""
from __future__ import annotations

import sys
import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope='session')
def qapp():
    """Geef een bestaande QApplication terug of maak er één aan."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
