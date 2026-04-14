"""ExportManager: PNG- en PDF-export van matplotlib-figuren."""

from __future__ import annotations
from pathlib import Path
from matplotlib.figure import Figure


class ExportManager:
    """Beheert export van visualisaties naar verschillende bestandsformaten."""

    def export_png(self, figure: Figure, filepath: str | Path, dpi: int = 150) -> None:
        """Exporteer een matplotlib-figuur als PNG-bestand.

        Parameters
        ----------
        figure:   De te exporteren matplotlib Figure.
        filepath: Doelbestandspad.
        dpi:      Resolutie in dots per inch.
        """
        figure.savefig(str(filepath), format='png', dpi=dpi, bbox_inches='tight')

