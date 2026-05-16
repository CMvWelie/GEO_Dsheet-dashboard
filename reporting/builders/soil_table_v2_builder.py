"""SoilTableV2Builder - bouwt de Grondsoortentabel v2 voor rapportage."""

from __future__ import annotations

from parsers.models import Project, Soil, SoilProfile, Stage, Surface
from reporting.models import ReportSection, ReportTable, TextBlock
from utils.formatting import fmt_number
from utils.geometry import surface_y_at

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

_METHODE_LABELS: dict[int, str] = {
    1: 'Ka / K0 / Kp',
    2: 'c, \u03c6, \u03b4 (Culmann)',
}
_METHODE_KOLOMMEN: list[str] = ['Fase', 'Methode links', 'Methode rechts']

_KKK_KOLOMMEN: list[str] = ['Grondsoort', 'Ka', 'K0', 'Kp']
_KKK_EENHEDEN: list[tuple[str, int]] = [('', 1), ('[-]', 3)]

_FASE_KOLOMMEN: list[str] = [
    'Laag',
    'b.k. laag',
    'o.k. laag',
    'Laag',
    'b.k. laag',
    'o.k. laag',
]

_FASE_KOLOMMEN_ENKEL: list[str] = [
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


def _find_surface(surfaces: list[Surface], naam: str) -> Surface | None:
    """Zoek een surface op naam in een surfacelijst."""
    return next((surface for surface in (surfaces or []) if surface.name == naam), None)


def _stage_surface(project: Project, fase: Stage, zijde: str) -> Surface | None:
    """Geef de surface die de doorsnede voor deze fasezijde gebruikt."""
    naam = fase.right_surface if zijde == 'rechts' else fase.left_surface
    gevonden = _find_surface(project.surfaces, naam)
    if gevonden:
        return gevonden
    if zijde == 'rechts' and len(project.surfaces) > 1:
        return project.surfaces[1]
    return project.surfaces[0] if project.surfaces else None


def _hoogste_surface_niveau(surface: Surface | None) -> float | None:
    """Geef het hoogste niveau van een surfaceline, inclusief x=0."""
    if not surface or not surface.points:
        return None
    xs = {
        0.0,
        *[
            float(p['x'])
            for p in surface.points
            if p.get('x') is not None
        ],
    }
    if not xs:
        return None
    return max(surface_y_at(surface.points, x) for x in xs)


def _laag_volledig_afgedekt(
    profiel: SoilProfile,
    index: int,
    surface: Surface | None,
) -> bool:
    """Bepaal of een laag nergens door de surface heen zichtbaar is."""
    if index + 1 >= len(profiel.layers) or not surface or not surface.points:
        return False
    hoogste_surface = _hoogste_surface_niveau(surface)
    if hoogste_surface is None:
        return False
    return hoogste_surface <= profiel.layers[index + 1].level + 1e-6


def _laag_zichtbaarheids_sleutels(
    profiel: SoilProfile | None,
    surface: Surface | None,
) -> list[tuple[float, str, bool]]:
    """Geef een vergelijkbare sleutel per laag inclusief zichtbaarheid."""
    if not profiel:
        return []
    return [
        (laag.level, laag.material, _laag_volledig_afgedekt(profiel, index, surface))
        for index, laag in enumerate(profiel.layers)
    ]


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

        grondsoorten_sec = self._bouw_grondsoorten_sectie(project)
        groepen = self._fase_groepen(project)

        if (
            len(groepen) == 1
            and self._fase_zijden_gelijk(groepen[0]['fase_ref'], project)
        ):
            namen = groepen[0]['namen']
            grondsoorten_sec.text_blocks.append(TextBlock(
                id='grondsoorten_v2_fase_intro',
                section=grondsoorten_sec.id,
                generated_text=_fase_intro(namen),
                source=_fase_titel(namen),
            ))
            return [grondsoorten_sec]

        return [grondsoorten_sec] + self._bouw_fase_secties(project)

    def _alle_methodes_cphi(self, project: Project) -> bool:
        """Geef True als alle fases uitsluitend methode 2 (c,φ,δ) gebruiken."""
        return bool(project.stages) and all(
            fase.method_left == 2 and fase.method_right == 2
            for fase in project.stages
        )

    def _bouw_grondsoorten_sectie(self, project: Project) -> ReportSection:
        """Bouw het unieke grondsoortenoverzicht."""
        sec = ReportSection(
            id='grondsoorten_v2_overzicht',
            title='Grondsoortentabel v2 - Grondsoorten',
        )
        if project.stages:
            sec.tables.append(self._bouw_berekeningsmethode_tabel(project))
        if not self._alle_methodes_cphi(project):
            sec.tables.append(self._bouw_kkk_tabel(project))
        sec.tables.append(ReportTable(
            id='grondsoorten_v2_overzicht_tabel',
            title='Grondsoorten',
            columns=_GRONDSOORT_KOLOMMEN,
            rows=self._grondsoorten_rijen(project),
        ))
        return sec

    def _bouw_berekeningsmethode_tabel(self, project: Project) -> ReportTable:
        """Bouw de berekeningsmethode-tabel per fase."""
        rijen = [
            [
                fase.name,
                _METHODE_LABELS.get(fase.method_left, str(fase.method_left)),
                _METHODE_LABELS.get(fase.method_right, str(fase.method_right)),
            ]
            for fase in project.stages
        ]
        return ReportTable(
            id='grondsoorten_v2_berekeningsmethode_tabel',
            title='Berekeningsmethode',
            columns=_METHODE_KOLOMMEN,
            rows=rijen,
        )

    def _bouw_kkk_tabel(self, project: Project) -> ReportTable:
        """Bouw de Ka/K0/Kp-tabel voor alle gebruikte grondsoorten."""
        gebruikte = {
            laag.material
            for profiel in project.profiles
            for laag in profiel.layers
        }
        soils = [s for s in project.soils if s.name in gebruikte]
        rijen = [
            [
                soil.name,
                fmt_number(soil.ka, 2),
                fmt_number(soil.kn, 2),
                fmt_number(soil.kp, 2),
            ]
            for soil in soils
        ]
        return ReportTable(
            id='grondsoorten_v2_kkk_tabel',
            title='Gronddrukcoëfficiënten',
            columns=_KKK_KOLOMMEN,
            rows=rijen,
            unit_groups=_KKK_EENHEDEN,
        )

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
        vorige_l: tuple = ()
        vorige_r: tuple = ()

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
            sleutel_l = tuple(_laag_zichtbaarheids_sleutels(
                prof_map.get(fase.left_profile),
                _stage_surface(project, fase, 'links'),
            ))
            sleutel_r = tuple(_laag_zichtbaarheids_sleutels(
                prof_map.get(fase.right_profile),
                _stage_surface(project, fase, 'rechts'),
            ))
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
        zijden_gelijk = self._fase_zijden_gelijk(fase, project)
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
            columns=(
                _FASE_KOLOMMEN_ENKEL
                if zijden_gelijk
                else _FASE_KOLOMMEN
            ),
            rows=self._fase_rijen(
                fase,
                project,
                links_ongewijzigd,
                rechts_ongewijzigd,
            ),
            column_groups=self._fase_kolomgroepen(fase, project),
            separator_before_cols=[] if zijden_gelijk else [3],
            strikethrough_cells=self._fase_doorhaal_cellen(
                fase,
                project,
                links_ongewijzigd,
                rechts_ongewijzigd,
            ),
        ))
        return sec

    def _fase_zijden_gelijk(self, fase: Stage, project: Project) -> bool:
        """Geef aan of links en rechts exact dezelfde grondlaagrijen hebben."""
        links_profiel = _find_profiel(project.profiles, fase.left_profile)
        rechts_profiel = _find_profiel(project.profiles, fase.right_profile)
        links_surface = _stage_surface(project, fase, 'links')
        rechts_surface = _stage_surface(project, fase, 'rechts')
        links = self._laag_rijen(links_profiel, links_surface)
        rechts = self._laag_rijen(rechts_profiel, rechts_surface)
        links_doorgehaald = self._laag_doorgehaald(links_profiel, links_surface)
        rechts_doorgehaald = self._laag_doorgehaald(rechts_profiel, rechts_surface)
        return bool(links) and (
            list(zip(links, links_doorgehaald))
            == list(zip(rechts, rechts_doorgehaald))
        )

    def _fase_kolomgroepen(
        self,
        fase: Stage,
        project: Project,
    ) -> list[tuple[str, int]]:
        """Geef de kolomgroepen voor een faselaagentabel."""
        if self._fase_zijden_gelijk(fase, project):
            return [('Grondlagen', 3)]
        return [
            ('Grondlagen linkerzijde', 3),
            ('Grondlagen rechterzijde', 3),
        ]

    def _fase_rijen(
        self,
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool,
        rechts_ongewijzigd: bool,
    ) -> list[list[str]]:
        """Bouw gecombineerde links/rechts-rijen voor een faselaagentabel."""
        links_profiel = _find_profiel(project.profiles, fase.left_profile)
        rechts_profiel = _find_profiel(project.profiles, fase.right_profile)
        links_surface = _stage_surface(project, fase, 'links')
        rechts_surface = _stage_surface(project, fase, 'rechts')
        links = self._laag_rijen(links_profiel, links_surface)
        rechts = self._laag_rijen(rechts_profiel, rechts_surface)
        links_doorgehaald = self._laag_doorgehaald(links_profiel, links_surface)
        rechts_doorgehaald = self._laag_doorgehaald(rechts_profiel, rechts_surface)
        zijden_gelijk = bool(links) and (
            list(zip(links, links_doorgehaald))
            == list(zip(rechts, rechts_doorgehaald))
        )
        geheel_ongewijzigd = links_ongewijzigd and rechts_ongewijzigd

        if zijden_gelijk:
            n_data = max(len(links), 1)
        elif links_ongewijzigd:
            n_data = max(len(rechts), 1)
        elif rechts_ongewijzigd:
            n_data = max(len(links), 1)
        else:
            n_data = max(len(links), len(rechts), 1)

        if zijden_gelijk:
            return self._zijde_rijen(links, geheel_ongewijzigd, n_data)

        links_data = self._zijde_rijen(links, links_ongewijzigd, n_data)
        rechts_data = self._zijde_rijen(rechts, rechts_ongewijzigd, n_data)
        return [links_data[i] + rechts_data[i] for i in range(n_data)]

    def _fase_doorhaal_cellen(
        self,
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool,
        rechts_ongewijzigd: bool,
    ) -> list[list[bool]]:
        """Bouw per cel de doorhaalstatus voor een faselaagentabel."""
        links_profiel = _find_profiel(project.profiles, fase.left_profile)
        rechts_profiel = _find_profiel(project.profiles, fase.right_profile)
        links_surface = _stage_surface(project, fase, 'links')
        rechts_surface = _stage_surface(project, fase, 'rechts')
        links = self._laag_rijen(links_profiel, links_surface)
        rechts = self._laag_rijen(rechts_profiel, rechts_surface)
        links_doorgehaald = self._laag_doorgehaald(links_profiel, links_surface)
        rechts_doorgehaald = self._laag_doorgehaald(rechts_profiel, rechts_surface)
        zijden_gelijk = bool(links) and (
            list(zip(links, links_doorgehaald))
            == list(zip(rechts, rechts_doorgehaald))
        )
        geheel_ongewijzigd = links_ongewijzigd and rechts_ongewijzigd

        if zijden_gelijk:
            n_data = max(len(links), 1)
            return self._zijde_doorhaal_cellen(
                links_doorgehaald,
                geheel_ongewijzigd,
                n_data,
            )
        if links_ongewijzigd:
            n_data = max(len(rechts), 1)
        elif rechts_ongewijzigd:
            n_data = max(len(links), 1)
        else:
            n_data = max(len(links), len(rechts), 1)
        links_cellen = self._zijde_doorhaal_cellen(
            links_doorgehaald,
            links_ongewijzigd,
            n_data,
        )
        rechts_cellen = self._zijde_doorhaal_cellen(
            rechts_doorgehaald,
            rechts_ongewijzigd,
            n_data,
        )
        return [links_cellen[i] + rechts_cellen[i] for i in range(n_data)]

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

    def _zijde_doorhaal_cellen(
        self,
        doorgestreept: list[bool],
        ongewijzigd: bool,
        n_data: int,
    ) -> list[list[bool]]:
        """Geef driekoloms-doorhaalstatussen voor een tabelzijde."""
        if ongewijzigd:
            return [[False, False, False] for _ in range(n_data)]
        return [
            [doorgestreept[i]] * 3 if i < len(doorgestreept) else [False, False, False]
            for i in range(n_data)
        ]

    def _laag_rijen(
        self,
        profiel: SoilProfile | None,
        surface: Surface | None = None,
    ) -> list[list[str]]:
        """Geef rijen ``[laagnaam, b.k. niveau, o.k. niveau]`` per laag."""
        if not profiel:
            return []
        rijen: list[list[str]] = []
        n = len(profiel.layers)
        doorgestreept = self._laag_doorgehaald(profiel, surface)
        eerste_zichtbaar = next(
            (index for index, afgedekt in enumerate(doorgestreept) if not afgedekt),
            None,
        )
        hoogste_surface = _hoogste_surface_niveau(surface)
        for i, laag in enumerate(profiel.layers):
            bk_niveau = (
                hoogste_surface
                if i == eerste_zichtbaar and hoogste_surface is not None
                else laag.level
            )
            bk = fmt_number(bk_niveau, 2)
            ok = fmt_number(profiel.layers[i + 1].level, 2) if i + 1 < n else 'Max'
            rijen.append([laag.material, bk, ok])
        return rijen

    def _laag_doorgehaald(
        self,
        profiel: SoilProfile | None,
        surface: Surface | None,
    ) -> list[bool]:
        """Geef per laag aan of deze volledig door de surface is afgedekt."""
        if not profiel:
            return []
        return [
            _laag_volledig_afgedekt(profiel, index, surface)
            for index, _laag in enumerate(profiel.layers)
        ]
