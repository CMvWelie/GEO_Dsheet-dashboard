"""Entry point voor de D-Sheet Dashboard applicatie."""

import sys
import os

# Zorg dat het projectpakket vindbaar is
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
except ImportError:
    try:
        from PySide6.QtWidgets import QApplication   # type: ignore
        from PySide6.QtCore import Qt                # type: ignore
    except ImportError:
        print('Fout: PyQt6 of PySide6 is niet geïnstalleerd.')
        print('Installeer met: pip install PyQt6')
        sys.exit(1)

from app.main_window import MainWindow


def main() -> None:
    """Start de D-Sheet Dashboard applicatie."""
    app = QApplication(sys.argv)
    app.setApplicationName('D-Sheet Dashboard')
    app.setOrganizationName('DKIB Geotechniek')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
