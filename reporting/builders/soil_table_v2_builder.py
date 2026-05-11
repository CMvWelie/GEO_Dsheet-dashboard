"""SoilTableV2Builder - bouwt de Grondsoortentabel v2 voor rapportage."""

from __future__ import annotations

from parsers.models import Project, Soil, SoilProfile, Stage
from reporting.models import ReportSection, ReportTable, TextBlock
from utils.formatting import fmt_number

_GRONDSOORT_KOLOMMEN: list[str] = [
    'Laag',
    '\u03b3d\n[kN/m\u00b3]',
    '\u03b3n\n[kN/m\u00b3]',
    "c'kar\n[kN/m\u00b2]",
    "\u03c6'kar\n[\u00b0]",
    '\u03b4\n[\u00b0]',
    'kh1',
    'kh2',
    'kh3',
]

_FASE_KOLOMMEN: list[str] = [
    'Laag',
    'b.k. laag',
    'o.k. laag',
    'Laag',
    'b.k. laag',
    'o.k. laag',
]


def _find_profiel(profielen: list[SoilProfile], naam: str) -> SoilProfile | None:
    """Zoek een profiel op naam in een profielenlijst."""
    return next((p for p in (profielen or []) if p.name == naam), None)


def _laag_sleutels(profiel: SoilProfile | None) -> list[tuple[float, str]]:
    """Geef een vergelijkbare sleutel per laag: ``(level, material)``."""
    if not profiel:
        return []
    return [(laag.level, laag.material) for laag in profiel.layers]


def _fase_titel(namen: list[str]) -> str:
    """Bouw de oude sectietitel op uit een of meerdere fasenamen."""
    if len(namen) == 1:
        return f'Grondlagen fase: "{namen[0]}"'
    hoofd = ', '.join(f'"{naam}"' for naam in namen[:-1])
    return f'Grondlagen fases: {hoofd} & "{namen[-1]}"'


def _fase_intro(namen: list[str]) -> str:
    """Bouw de introzin en eventuele faselijst voor een grondlaagopbouw."""
    if len(namen) == 1:
        return f'In de fase "{namen[0]}" wordt het volgende profiel gehanteerd:'
    regels = ['Het volgende profiel wordt gehanteerd in de volgende fases:']
    regels.extend(namen)
    return '\n'.join(regels)


def _kh_waarde(waarde: float) -> str:
    """Formatteer een horizontale beddingsconstante voor de rapporttabel."""
    return str(int(waarde)) if waarde else '-'


class SoilTableV2Builder:
    """Bouwt het grondsoortenoverzicht en de gegroepeerde faselaagentabellen."""

    def build(self, project: Project) -> list[ReportSection]:
        """Bouw de Grondsoortentabel v2-secties.

        Parameters
        ----------
        project:
            Actief project met grondsoorten, profielen en constructiefases.

        Returns
        -------
        list[ReportSection]
            Eerst het unieke grondsoortenoverzicht, daarna een sectie per
            aaneengesloten fasegroep met gelijke grondopbouw.
        """
        if not project.soils:
            return []

        secties = [self._bouw_grondsoorten_sectie(project)]
        secties.extend(self._bouw_fase_secties(project))
        return secties

    def _bouw_grondsoorten_sectie(self, project: Project) -> ReportSection:
        """Bouw het unieke grondsoortenoverzicht."""
        sec = ReportSection(
            id='grondsoorten_v2_overzicht',
            title='Grondsoortentabel v2 - Grondsoorten',
        )
        sec.tables.append(ReportTable(
            id='grondsoorten_v2_overzicht_tabel',
            title='',
            columns=_GRONDSOORT_KOLOMMEN,
            rows=self._grondsoorten_rijen(project),
        ))
        return sec

    def _grondsoorten_rijen(self, project: Project) -> list[list[str]]:
        """Geef tabelrijen voor alle gebruikte grondsoorten."""
        gebruikte = {
            laag.material
            for profiel in project.profiles
            for laag in profiel.layers
        }
        soils = [soil for soil in project.soils if soil.name in gebruikte]
        return [self._grondsoort_rij(soil) for soil in soils]

    def _grondsoort_rij(self, soil: Soil) -> list[str]:
        """Geef een rapporttabelrij voor een grondsoort."""
        return [
            soil.name,
            fmt_number(soil.gamma_dry),
            fmt_number(soil.gamma_wet),
            fmt_number(soil.cohesion),
            fmt_number(soil.phi),
            fmt_number(soil.delta),
            _kh_waarde(soil.kh1),
            _kh_waarde(soil.kh2),
            _kh_waarde(soil.kh3),
        ]

    def _bouw_fase_secties(self, project: Project) -> list[ReportSection]:
        """Bouw een faselaagsectie per aaneengesloten groep gelijke profielen."""
        groepen = self._fase_groepen(project)
        secties: list[ReportSection] = []
        vorige_l: tuple[tuple[float, str], ...] = ()
        vorige_r: tuple[tuple[float, str], ...] = ()

        for index, groep in enumerate(groepen, start=1):
            links_ongewijzigd = bool(vorige_l) and groep['sleutel_l'] == vorige_l
            rechts_ongewijzigd = bool(vorige_r) and groep['sleutel_r'] == vorige_r
            secties.append(self._bouw_fase_sectie(
                index,
                groep['namen'],
                groep['fase_ref'],
                project,
                links_ongewijzigd,
                rechts_ongewijzigd,
            ))
            vorige_l = groep['sleutel_l']
            vorige_r = groep['sleutel_r']

        return secties

    def _fase_groepen(self, project: Project) -> list[dict]:
        """Groepeer opeenvolgende fases met dezelfde linker- en rechteropbouw."""
        prof_map = {profiel.name: profiel for profiel in project.profiles}
        groepen: list[dict] = []
        for fase in project.stages:
            sleutel_l = tuple(_laag_sleutels(prof_map.get(fase.left_profile)))
            sleutel_r = tuple(_laag_sleutels(prof_map.get(fase.right_profile)))
            sleutel = (sleutel_l, sleutel_r)
            if groepen and groepen[-1]['sleutel'] == sleutel:
                groepen[-1]['namen'].append(fase.name)
            else:
                groepen.append({
                    'sleutel': sleutel,
                    'sleutel_l': sleutel_l,
                    'sleutel_r': sleutel_r,
                    'namen': [fase.name],
                    'fase_ref': fase,
                })
        return groepen

    def _bouw_fase_sectie(
        self,
        index: int,
        namen: list[str],
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool,
        rechts_ongewijzigd: bool,
    ) -> ReportSection:
        """Bouw een sectie met linker- en rechtergrondlagen voor een fasegroep."""
        sec = ReportSection(
            id=f'grondsoorten_v2_fase_{index}',
            title='Grondlaagopbouw fases' if index == 1 else '',
        )
        sec.text_blocks.append(TextBlock(
            id=f'grondsoorten_v2_fase_{index}_intro',
            section=sec.id,
            generated_text=_fase_intro(namen),
            source=_fase_titel(namen),
        ))
        sec.tables.append(ReportTable(
            id=f'grondsoorten_v2_fase_{index}_tabel',
            title='',
            columns=_FASE_KOLOMMEN,
            rows=self._fase_rijen(
                fase,
                project,
                links_ongewijzigd,
                rechts_ongewijzigd,
            ),
            column_groups=[
                ('Grondlagen linkerzijde', 3),
                ('Grondlagen rechterzijde', 3),
            ],
            separator_before_cols=[3],
        ))
        return sec

    def _fase_rijen(
        self,
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool,
        rechts_ongewijzigd: bool,
    ) -> list[list[str]]:
        """Bouw gecombineerde links/rechts-rijen voor een faselaagentabel."""
        links = self._laag_rijen(_find_profiel(project.profiles, fase.left_profile))
        rechts = self._laag_rijen(_find_profiel(project.profiles, fase.right_profile))

        if links_ongewijzigd:
            n_data = max(len(rechts), 1)
        elif rechts_ongewijzigd:
            n_data = max(len(links), 1)
        else:
            n_data = max(len(links), len(rechts), 1)

        links_data = self._zijde_rijen(links, links_ongewijzigd, n_data)
        rechts_data = self._zijde_rijen(rechts, rechts_ongewijzigd, n_data)
        return [links_data[i] + rechts_data[i] for i in range(n_data)]

    def _zijde_rijen(
        self,
        rijen: list[list[str]],
        ongewijzigd: bool,
        n_data: int,
    ) -> list[list[str]]:
        """Geef driekolomsrijen voor een tabelzijde."""
        if ongewijzigd:
            melding = 'Grondopbouw ongewijzigd t.o.v. vorige fase'
            return [[melding, '', '']] + [['', '', ''] for _ in range(n_data - 1)]

        return [
            rijen[i] if i < len(rijen) else ['', '', '']
            for i in range(n_data)
        ]

    def _laag_rijen(self, profiel: SoilProfile | None) -> list[list[str]]:
        """Geef rijen ``[laagnaam, b.k. niveau, o.k. niveau]`` per laag."""
        if not profiel:
            return []
        rijen: list[list[str]] = []
        n = len(profiel.layers)
        for i, laag in enumerate(profiel.layers):
            bk = fmt_number(laag.level, 2)
            ok = fmt_number(profiel.layers[i + 1].level, 2) if i + 1 < n else 'Max'
            rijen.append([laag.material, bk, ok])
        return rijen
