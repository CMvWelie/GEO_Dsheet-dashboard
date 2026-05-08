"""Maak een Windows-bureaubladsnelkoppeling voor D-Sheet Dashboard.

Eenmalig uitvoeren: python maak_snelkoppeling.py

Genereert themes/Dsheet_dashboard.ico (vanuit de PNG) en plaatst een
snelkoppeling met het juiste icoon op het bureaublad.
"""

from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PNG_PAD = ROOT / 'themes' / 'Dsheet_dashboard.png'
ICO_PAD = ROOT / 'themes' / 'Dsheet_dashboard.ico'
RUN_PAD = ROOT / 'run.pyw'
PYTHONW = Path(sys.executable).parent / 'pythonw.exe'


def _maak_ico(png_pad: Path, ico_pad: Path) -> None:
    """Wikkel een PNG in een ICO-container (Windows ondersteunt embedded PNG)."""
    png_data = png_pad.read_bytes()
    # ICO-header: reserved=0, type=1 (icon), count=1
    header = struct.pack('<HHH', 0, 1, 1)
    # Directory-entry: breedte/hoogte 0 = 256 px, 1 plane, 32-bit, offset=22
    dir_entry = struct.pack('<BBBBHHII', 0, 0, 0, 0, 1, 32, len(png_data), 22)
    ico_pad.write_bytes(header + dir_entry + png_data)
    print(f'ICO aangemaakt: {ico_pad}')


def _maak_snelkoppeling(lnk_pad: Path) -> None:
    """Maak een .lnk-bestand via PowerShell WScript.Shell."""
    ps = (
        f'$s = (New-Object -ComObject WScript.Shell).CreateShortcut("{lnk_pad}");'
        f'$s.TargetPath = "{PYTHONW}";'
        f'$s.Arguments = \'"{RUN_PAD}"\';'
        f'$s.IconLocation = "{ICO_PAD}";'
        f'$s.WorkingDirectory = "{ROOT}";'
        f'$s.Description = "D-Sheet Dashboard";'
        f'$s.Save()'
    )
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', ps],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f'Fout bij aanmaken snelkoppeling:\n{result.stderr}')
        sys.exit(1)
    print(f'Snelkoppeling aangemaakt: {lnk_pad}')


def main() -> None:
    if not PNG_PAD.exists():
        print(f'Fout: logo niet gevonden op {PNG_PAD}')
        sys.exit(1)
    if not PYTHONW.exists():
        print(f'Fout: pythonw.exe niet gevonden op {PYTHONW}')
        sys.exit(1)

    _maak_ico(PNG_PAD, ICO_PAD)

    bureaublad = Path.home() / 'Desktop'
    _maak_snelkoppeling(bureaublad / 'D-Sheet Dashboard.lnk')

    print('Klaar. De snelkoppeling staat op het bureaublad.')


if __name__ == '__main__':
    main()
