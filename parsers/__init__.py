"""Parser-pakket met plugin-registry voor D-Sheet bestandsformaten."""

from __future__ import annotations
from typing import Callable, Type

# Registry: extensie → parser-callable
_registry: dict[str, Callable] = {}


def register_parser(extension: str, parser_callable: Callable) -> None:
    """Registreer een parser voor een bestandsextensie.

    Parameters
    ----------
    extension:        Bestandsextensie zonder punt (bijv. 'shi', 'plx').
    parser_callable:  Functie of klasse die (text: str, base_name: str) → Project aanneemt.
    """
    _registry[extension.lower()] = parser_callable


def get_parser(extension: str) -> Callable | None:
    """Geef de geregistreerde parser terug voor de opgegeven extensie.

    Parameters
    ----------
    extension: Bestandsextensie zonder punt.

    Returns
    -------
    Callable | None  Parser-callable, of None als niet gevonden.
    """
    return _registry.get(extension.lower())


# Registreer de ingebouwde D-Sheet parser
from parsers.shi_parser import parse_project  # noqa: E402
from parsers.models import FileBundle         # noqa: E402

def _dsheet_parser(file_bundle: FileBundle, base_name: str):
    return parse_project(file_bundle, base_name)

register_parser('shi', _dsheet_parser)
register_parser('shd', _dsheet_parser)
register_parser('shs', _dsheet_parser)
