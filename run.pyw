"""Entry point voor de D-Sheet Dashboard applicatie."""

import sys
import os
import ctypes
from pathlib import Path

# Zorg dat het projectpakket vindbaar is
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows: eigen app-identiteit zodat de taakbalk het venster-icoon toont
# in plaats van het python.exe-icoon.
if sys.platform == 'win32':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        'DKIB.DsheetDashboard.1'
    )

# ------------------------------------------------------------------
# Dependency-controle bij opstarten
# ------------------------------------------------------------------
_VEREISTE_PAKKETTEN = [
    ('PyQt6',       'pip install PyQt6'),
    ('matplotlib',  'pip install matplotlib'),
    ('openpyxl',    'pip install openpyxl'),
    ('docx',        'pip install python-docx'),
]
_ontbrekend = []
for _pkg, _installeer in _VEREISTE_PAKKETTEN:
    try:
        __import__(_pkg)
    except ImportError:
        _ontbrekend.append(f'  • {_pkg:12s}  →  {_installeer}')

if _ontbrekend:
    print('Fout: de volgende pakketten ontbreken. Installeer ze en start opnieuw.')
    print('\n'.join(_ontbrekend))
    sys.exit(1)

try:
    from PyQt6.QtWidgets import QApplication, QSplashScreen
    from PyQt6.QtCore import Qt, QTimer, QByteArray
    from PyQt6.QtGui import QPixmap, QIcon
except ImportError:
    try:
        from PySide6.QtWidgets import QApplication, QSplashScreen  # type: ignore
        from PySide6.QtCore import Qt                               # type: ignore
        from PySide6.QtGui import QPixmap                           # type: ignore
    except ImportError:
        print('Fout: PyQt6 of PySide6 is niet geïnstalleerd.')
        print('Installeer met: pip install PyQt6')
        sys.exit(1)

from app.config_manager import ConfigManager
from app.main_window import MainWindow
from app.theme_apply import bootstrap_theme

_LOGO_PAD = Path(__file__).parent / 'themes' / 'Dsheet_dashboard.png'


def main() -> None:
    """Start de D-Sheet Dashboard applicatie."""
    app = QApplication(sys.argv)
    app.setApplicationName('D-Sheet Dashboard')
    app.setOrganizationName('DKIB Geotechniek')
    if _LOGO_PAD.exists():
        app.setWindowIcon(QIcon(str(_LOGO_PAD)))

    # Splash screen tonen vóór het zware laden van het hoofdvenster
    splash: QSplashScreen | None = None
    pixmap = QPixmap(str(_LOGO_PAD))
    if not pixmap.isNull():
        pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()

    # Lees actief-thema-naam uit config (default 'DKIB' bij ontbreken)
    _, _, app_settings = ConfigManager().load()
    thema = bootstrap_theme(app_settings.active_theme_name)

    window = MainWindow(thema=thema)
    window.show()
    if app_settings.window_geometry:
        window.restoreGeometry(QByteArray.fromBase64(
            app_settings.window_geometry.encode('ascii')
        ))

    # Splash sluiten zodra het hoofdvenster zichtbaar is
    if splash is not None:
        splash.finish(window)

    # Bestanden meegegeven via commandoregel (bijv. dubbelklik vanuit Verkenner)
    cli_paden = [p for p in sys.argv[1:] if Path(p).is_file()]
    if cli_paden:
        QTimer.singleShot(0, lambda: window.open_cli_bestanden(cli_paden))

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
