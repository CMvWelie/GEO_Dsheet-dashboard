"""SessionManager — opslaan en laden van .dsd-sessiebestanden."""

from __future__ import annotations

import json
from pathlib import Path

from app.session_state import SessionData

DSD_EXTENSIE = '.dsd'


class SessionManager:
    """Serialiseert en deserialiseert sessiebestanden naar JSON.

    Heeft geen Qt-afhankelijkheden; retourneert status-tuples.
    """

    def opslaan(self, pad: Path, data: SessionData) -> tuple[bool, str]:
        """Sla sessiedata op naar ``pad``.

        Parameters
        ----------
        pad:
            Doelbestandspad (`.dsd`-extensie aanbevolen).
        data:
            Te serialiseren sessiedata.

        Returns
        -------
        tuple[bool, str]
            ``(True, '')`` bij succes; ``(False, foutmelding)`` anders.
        """
        try:
            pad.parent.mkdir(parents=True, exist_ok=True)
            with open(pad, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
            return True, ''
        except Exception as exc:
            return False, str(exc)

    def laden(self, pad: Path) -> tuple[SessionData | None, str]:
        """Laad sessiedata van ``pad``.

        Parameters
        ----------
        pad:
            Pad naar het `.dsd`-bestand.

        Returns
        -------
        tuple[SessionData | None, str]
            ``(SessionData, '')`` bij succes; ``(None, foutmelding)`` anders.
        """
        if not pad.exists():
            return None, f'Bestand bestaat niet: {pad}'
        try:
            with open(pad, encoding='utf-8') as f:
                d = json.load(f)
            return SessionData.from_dict(d), ''
        except json.JSONDecodeError as exc:
            return None, f'Ongeldig JSON in sessiebestand: {exc}'
        except Exception as exc:
            return None, f'Fout bij laden sessie: {exc}'
