"""SoilTableBuilder — bouwt grondsoortentabellen als ReportSection per profiel."""

from __future__ import annotations

import re

from parsers.models import Project, Soil, SoilProfile
from reporting.models import ReportSection, ReportTable
from utils.formatting import fmt_number

_KOLOMMEN: list[str] = [
    'BK laag [m NAP]',
    'OK laag [m NAP]',
    'Laag',
    '\u03b3d [kN/m\u00b3]',
    '\u03b3n [kN/m\u00b3]',
    "c'kar [kN/m\u00b2]",
    "\u03c6'kar [\u00b0]",
    '\u03b4 [\u00b0]',
    'kh1',
    'kh2',
    'kh3',
]


class SoilTableBuilder:
    """Bouwt een ReportSection per grondprofiel met alle grondparameters."""

    def build(self, project: Project) -> list[ReportSection]:
        """Bouw één ReportSection per profiel.

        Parameters
        ----------
        project:
            Actief project met profielen en grondsoorten.

        Returns
        -------
        list[ReportSection]
            Één sectie per profiel, lege lijst als er geen profielen zijn.
        """
        soil_map: dict[str, Soil] = {s.name: s for s in project.soils}
        return [self._bouw_sectie(profiel, soil_map) for profiel in project.profiles]

    def _bouw_sectie(
        self, profiel: SoilProfile, soil_map: dict[str, Soil]
    ) -> ReportSection:
        """Bouw een ReportSection voor één grondprofiel."""
        sec_id = 'soil_table_' + re.sub(r'\s+', '_', profiel.name.lower())
        sec = ReportSection(id=sec_id, title=f'Grondsoortentabel \u2014 {profiel.name}')
        tabel = self._bouw_tabel(profiel, soil_map)
        tabel.id = f'{sec_id}_tabel'
        sec.tables.append(tabel)
        return sec

    def _bouw_tabel(
        self,
        profiel: SoilProfile,
        soil_map: dict[str, Soil],
    ) -> ReportTable:
        """Bouw de grondparametertabel voor één grondprofiel."""
        n = len(profiel.layers)
        rijen: list[list[str]] = []
        for i, laag in enumerate(profiel.layers):
            ok = fmt_number(profiel.layers[i + 1].level) if i + 1 < n else '-'
            soil = soil_map.get(laag.material)
            if soil:
                params: list[str] = [
                    fmt_number(soil.gamma_dry),
                    fmt_number(soil.gamma_wet),
                    fmt_number(soil.cohesion),
                    fmt_number(soil.phi),
                    fmt_number(soil.delta),
                    # kh=0 → '-': spiegelt gedrag van tab_grondsoorten (kh=0 betekent niet van toepassing in D-Sheet)
                    str(int(soil.kh1)) if soil.kh1 else '-',
                    str(int(soil.kh2)) if soil.kh2 else '-',
                    str(int(soil.kh3)) if soil.kh3 else '-',
                ]
            else:
                params = ['-'] * 8
            rijen.append([fmt_number(laag.level), ok, laag.material] + params)
        return ReportTable(
            id='',        # wordt gezet door _bouw_sectie
            title='',
            columns=_KOLOMMEN,
            rows=rijen,
        )
