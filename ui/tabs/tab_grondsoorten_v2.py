"""Tab Grondsoortentabel v2 — grondsoorten-overzicht + faselagen-tabellen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout,
    QSizePolicy,
)
# QVBoxLayout gebruikt door _build en grondsoortentabel; QGridLayout door fasetabellen
from PyQt6.QtCore import Qt

import ui.table_styles as _ts
from parsers.models import Project, SoilProfile, Stage
from utils.formatting import fmt_number

# Kolomstrekking voor de faselagen-tabel.
_FASE_COL_STRETCH = [4, 2, 2, 4, 2, 2]
_FASE_COL_STRETCH_ENKEL = [4, 2, 2]

_SOIL_COL0_W = 150   # ≈ 4 cm bij 96 dpi
_SOIL_COLN_W = 57    # ≈ 1,5 cm bij 96 dpi

_SOIL_KOLOMMEN: list[str] = [
    'Laag',
    'γd\n[kN/m³]',
    'γn\n[kN/m³]',
    "c'kar\n[kN/m²]",
    "φ'kar\n[°]",
    'δ\n[°]',
    'kh1',
    'kh2',
    'kh3',
]


def _find_profiel(profielen: list[SoilProfile], naam: str) -> SoilProfile | None:
    return next((p for p in (profielen or []) if p.name == naam), None)


def _laag_sleutels(profiel: SoilProfile | None) -> list[tuple]:
    """Geef een vergelijkbare sleutel per laag: (level, material)."""
    if not profiel:
        return []
    return [(l.level, l.material) for l in profiel.layers]


def _fase_intro(namen: list[str]) -> tuple[str, list[str]]:
    """Bouw de introtekst en eventuele faselijst voor een grondlaagopbouw."""
    if len(namen) == 1:
        return f'In de fase "{namen[0]}" wordt het volgende profiel gehanteerd:', []
    return 'Het volgende profiel wordt gehanteerd in de volgende fases:', namen


class TabGrondsoortenv2(QWidget):
    """Grondsoortenoverzicht + per-fase grondlaagentabellen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate(self, project: Project | None) -> None:
        """Vul de tab met grondsoortentabel en faselagen-tabellen.

        Parameters
        ----------
        project : Project | None
            Het actieve project, of None om de tab leeg te tonen.
        """
        self._project = project
        self._clear_content()

        if not project or not project.soils:
            self._render_leeg()
            return

        # Deel 1: unieke grondsoorten
        self._voeg_sectie_kop_toe('Grondsoorten')
        self._content_layout.insertWidget(
            self._content_layout.count() - 1,
            self._maak_grondsoorten_tabel(project),
        )

        # Deel 2: groepeer aaneengesloten identieke fases, toon één tabel per groep
        prof_map = {pr.name: pr for pr in project.profiles}

        # Bouw groepen van opeenvolgende fases met dezelfde laagsamenstelling
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

        vorige_l: tuple = ()
        vorige_r: tuple = ()
        for index, groep in enumerate(groepen):
            namen = groep['namen']
            if index == 0:
                self._voeg_sectie_kop_toe('Grondlaagopbouw fases')
            else:
                self._voeg_witregel_toe()
            self._voeg_fase_intro_toe(namen, witregel_na=bool(index))
            links_ongewijzigd = bool(vorige_l) and groep['sleutel_l'] == vorige_l
            rechts_ongewijzigd = bool(vorige_r) and groep['sleutel_r'] == vorige_r
            widget: QWidget = self._maak_fase_tabel(
                groep['fase_ref'], project, links_ongewijzigd, rechts_ongewijzigd
            )
            self._content_layout.insertWidget(self._content_layout.count() - 1, widget)
            vorige_l = groep['sleutel_l']
            vorige_r = groep['sleutel_r']

    # ------------------------------------------------------------------
    # Hulpmethoden
    # ------------------------------------------------------------------

    def _render_leeg(self) -> None:
        lbl = QLabel('Geen gronddata beschikbaar. Laad een project.')
        lbl.setStyleSheet(
            f'color: #7a93a8; font-size: 13px; '
            f'font-family: {_ts.TABLE_FONT}; padding: 32px 20px;'
        )
        self._content_layout.insertWidget(0, lbl)

    def _clear_content(self) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _voeg_sectie_kop_toe(self, naam: str) -> None:
        lbl = QLabel(naam)
        lbl.setStyleSheet(
            f'font-family: {_ts.TABLE_FONT}; font-size: 13px; font-weight: 600; '
            f'color: {_ts.TABLE_LABEL_COLOR}; background: transparent; '
            f'padding: 16px 4px 6px 4px;'
        )
        self._content_layout.insertWidget(self._content_layout.count() - 1, lbl)

    def _voeg_witregel_toe(self) -> None:
        """Voeg een compacte witregel toe tussen tekstblokken en tabellen."""
        spacer = QWidget()
        spacer.setFixedHeight(8)
        self._content_layout.insertWidget(self._content_layout.count() - 1, spacer)

    def _voeg_fase_intro_toe(
        self,
        namen: list[str],
        *,
        witregel_na: bool = False,
    ) -> None:
        """Voeg de toelichting bij een fasegroep toe boven de tabel."""
        intro, bullets = _fase_intro(namen)

        lbl = QLabel(intro)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f'font-family: {_ts.TABLE_FONT}; font-size: 12px; '
            f'color: {_ts.TABLE_VALUE_COLOR}; background: transparent; '
            f'padding: 0 4px 4px 4px;'
        )
        self._content_layout.insertWidget(self._content_layout.count() - 1, lbl)

        for fase_naam in bullets:
            bullet = QLabel(f'- {fase_naam}')
            bullet.setWordWrap(True)
            bullet.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 12px; '
                f'color: {_ts.TABLE_VALUE_COLOR}; background: transparent; '
                f'padding: 0 4px 2px 20px;'
            )
            self._content_layout.insertWidget(
                self._content_layout.count() - 1,
                bullet,
            )
        if bullets or witregel_na:
            self._voeg_witregel_toe()

    # ------------------------------------------------------------------
    # Grondsoorten-overzichtstabel (deel 1)
    # ------------------------------------------------------------------

    def _gebruikte_grondnamen(self, project: Project) -> set[str]:
        namen: set[str] = set()
        for profiel in project.profiles:
            for laag in profiel.layers:
                namen.add(laag.material)
        return namen

    def _maak_grondsoorten_tabel(self, project: Project) -> QWidget:
        gebruikte = self._gebruikte_grondnamen(project)
        soils = [s for s in project.soils if s.name in gebruikte]

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_ts.TABLE_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._maak_grondsoorten_header())

        for i, soil in enumerate(soils):
            bg = _ts.TABLE_ROW_ODD_BG if i % 2 == 0 else _ts.TABLE_ROW_EVEN_BG
            is_last = i == len(soils) - 1
            kh1 = str(int(soil.kh1)) if soil.kh1 else '-'
            kh2 = str(int(soil.kh2)) if soil.kh2 else '-'
            kh3 = str(int(soil.kh3)) if soil.kh3 else '-'
            waarden = [
                soil.name,
                fmt_number(soil.gamma_dry),
                fmt_number(soil.gamma_wet),
                fmt_number(soil.cohesion),
                fmt_number(soil.phi),
                fmt_number(soil.delta),
                kh1, kh2, kh3,
            ]
            layout.addWidget(self._maak_grondsoorten_rij(waarden, bg, is_last))

        return frame

    def _maak_grondsoorten_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_ts.TABLE_HEADER_SUB_BG};')
        grid = QGridLayout(hdr)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n = len(_SOIL_KOLOMMEN)
        for col, tekst in enumerate(_SOIL_KOLOMMEN):
            lbl = QLabel(tekst)
            lbl.setFixedWidth(_SOIL_COL0_W if col == 0 else _SOIL_COLN_W)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft
                if col == 0
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};'
                if col < n - 1 else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 5px 8px; {border_r}'
            )
            grid.addWidget(lbl, 0, col)

        return hdr

    def _maak_grondsoorten_rij(self, waarden: list[str], bg: str, is_last: bool) -> QWidget:
        rij = QWidget()
        grid = QGridLayout(rij)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        border_b = '' if is_last else f'border-bottom: 1px solid {_ts.TABLE_ROW_SEP};'

        for col, waarde in enumerate(waarden):
            lbl = QLabel(waarde)
            lbl.setFixedWidth(_SOIL_COL0_W if col == 0 else _SOIL_COLN_W)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft if col == 0
                else Qt.AlignmentFlag.AlignRight
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_ROW_SEP};'
                if col < len(waarden) - 1 else ''
            )
            kleur = _ts.TABLE_LABEL_COLOR if col == 0 else _ts.TABLE_VALUE_COLOR
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 12px; color: {kleur}; '
                f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
            )
            grid.addWidget(lbl, 0, col)

        return rij

    # ------------------------------------------------------------------
    # Fase-grondlaagentabel (deel 2)
    # ------------------------------------------------------------------

    def _maak_fase_tabel(
        self,
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool = False,
        rechts_ongewijzigd: bool = False,
    ) -> QWidget:
        """Bouw de faselaagentabel als één plat QGridLayout met rowspan-ondersteuning.

        Parameters
        ----------
        fase : Stage
            De te tonen constructiefase.
        project : Project
            Het actieve project.
        links_ongewijzigd : bool
            True als het linkerprofiel gelijk is aan de vorige fase.
        rechts_ongewijzigd : bool
            True als het rechterprofiel gelijk is aan de vorige fase.
        """
        links_profiel = _find_profiel(project.profiles, fase.left_profile)
        rechts_profiel = _find_profiel(project.profiles, fase.right_profile)
        links_rijen = self._laag_rijen(links_profiel)
        rechts_rijen = self._laag_rijen(rechts_profiel)
        zijden_gelijk = bool(links_rijen) and links_rijen == rechts_rijen
        geheel_ongewijzigd = links_ongewijzigd and rechts_ongewijzigd

        # Aantal datarijen: bepaald door de zijde die wél data toont
        if zijden_gelijk:
            n_data = max(len(links_rijen), 1)
        elif links_ongewijzigd:
            n_data = max(len(rechts_rijen), 1)
        elif rechts_ongewijzigd:
            n_data = max(len(links_rijen), 1)
        else:
            n_data = max(len(links_rijen), len(rechts_rijen), 1)

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_ts.TABLE_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        col_stretch = _FASE_COL_STRETCH_ENKEL if zijden_gelijk else _FASE_COL_STRETCH
        for col, stretch in enumerate(col_stretch):
            grid.setColumnStretch(col, stretch)

        if zijden_gelijk:
            self._voeg_fase_tabel_header_toe(grid, [(0, 'Grondlagen')], 3)
            self._voeg_fase_tabel_subkoppen_toe(grid, ['Laag', 'b.k. laag', 'o.k. laag'])
            self._vul_helft(
                grid,
                2,
                n_data,
                links_rijen,
                geheel_ongewijzigd,
                col_offset=0,
                links=False,
            )
            return self._verpak_halve_breedte(frame)

        # ── Headerrij 0: samengevoegde zijkoppen ─────────────────────
        for col_start, tekst in [
            (0, 'Grondlagen linkerzijde'),
            (3, 'Grondlagen rechterzijde'),
        ]:
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};' if col_start == 0 else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 10px; font-weight: 700; '
                f'color: {_ts.TABLE_HEADER_FG}; background: {_ts.TABLE_HEADER_BG}; '
                f'padding: 5px 8px; border-bottom: 1px solid {_ts.TABLE_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col_start, 1, 3)

        # ── Headerrij 1: kolomnamen ───────────────────────────────────
        subkoppen = ['Laag', 'b.k. laag', 'o.k. laag', 'Laag', 'b.k. laag', 'o.k. laag']
        for col, tekst in enumerate(subkoppen):
            lbl = QLabel(tekst)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft
                if col in (0, 3)
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};' if col < 5 else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 5px 8px; {border_r}'
            )
            grid.addWidget(lbl, 1, col)

        # ── Datarijen (vanaf gridrow 2) ───────────────────────────────
        self._vul_helft(
            grid,
            2,
            n_data,
            links_rijen,
            links_ongewijzigd,
            col_offset=0,
            links=True,
        )
        self._vul_helft(
            grid,
            2,
            n_data,
            rechts_rijen,
            rechts_ongewijzigd,
            col_offset=3,
            links=False,
        )

        return frame

    def _verpak_halve_breedte(self, tabel: QWidget) -> QWidget:
        """Plaats een verkorte fasetabel op halve breedte links in de tab."""
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(tabel, stretch=1)
        layout.addStretch(1)
        return wrapper

    def _voeg_fase_tabel_header_toe(
        self,
        grid: QGridLayout,
        groepen: list[tuple[int, str]],
        totaal_kolommen: int,
    ) -> None:
        """Voeg de samengevoegde groepkoppen aan een fasetabel toe."""
        for col_start, tekst in groepen:
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};'
                if col_start + 3 < totaal_kolommen else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 10px; font-weight: 700; '
                f'color: {_ts.TABLE_HEADER_FG}; background: {_ts.TABLE_HEADER_BG}; '
                f'padding: 5px 8px; border-bottom: 1px solid {_ts.TABLE_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col_start, 1, 3)

    def _voeg_fase_tabel_subkoppen_toe(
        self,
        grid: QGridLayout,
        subkoppen: list[str],
    ) -> None:
        """Voeg de kolomkoppen aan een fasetabel toe."""
        laatste_kolom = len(subkoppen) - 1
        for col, tekst in enumerate(subkoppen):
            lbl = QLabel(tekst)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft
                if col in (0, 3)
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};'
                if col < laatste_kolom else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 5px 8px; {border_r}'
            )
            grid.addWidget(lbl, 1, col)

    def _vul_helft(
        self,
        grid: QGridLayout,
        data_start: int,
        n_data: int,
        rijen: list[list[str]],
        ongewijzigd: bool,
        col_offset: int,
        links: bool,
    ) -> None:
        """Vul de linker- of rechterkant van de fase-tabel in het gedeelde grid.

        Parameters
        ----------
        grid : QGridLayout
            Het grid van de faselaagentabel.
        data_start : int
            Eerste gridrow voor data (= 2, na de twee headerrijen).
        n_data : int
            Totaal aantal datarijen in de tabel.
        rijen : list[list[str]]
            Laagdata [naam, bk, ok] per rij voor deze zijde.
        ongewijzigd : bool
            True → één samengevoegde cel met de 'ongewijzigd'-tekst.
        col_offset : int
            0 voor linkerzijde, 3 voor rechterzijde.
        links : bool
            True als dit de linkerzijde is (bepaalt de zware scheidingslijn rechts).
        """
        # Zware rand rechts van de linkerzijde (scheiding L/R)
        scheiding_r = (
            f'border-right: 1px solid {_ts.TABLE_BORDER};' if links else ''
        )

        if ongewijzigd:
            lbl = QLabel('Grondopbouw ongewijzigd t.o.v. vorige fase')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f'font-family: {_ts.TABLE_FONT}; font-size: 11px; font-style: italic; '
                f'color: {_ts.TABLE_LABEL_COLOR}; background: {_ts.TABLE_ROW_EVEN_BG}; '
                f'padding: 6px 8px; {scheiding_r}'
            )
            grid.addWidget(lbl, data_start, col_offset, n_data, 3)
            return

        for i in range(n_data):
            bg = _ts.TABLE_ROW_ODD_BG if i % 2 == 0 else _ts.TABLE_ROW_EVEN_BG
            border_b = (
                '' if i == n_data - 1
                else f'border-bottom: 1px solid {_ts.TABLE_ROW_SEP};'
            )
            rij = rijen[i] if i < len(rijen) else ['', '', '']
            for j, waarde in enumerate(rij):
                col = col_offset + j
                lbl = QLabel(waarde)
                is_naam = j == 0
                uitlijning = Qt.AlignmentFlag.AlignLeft if is_naam else Qt.AlignmentFlag.AlignRight
                lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                if links and j == 2:
                    border_r = scheiding_r
                elif j < 2:
                    border_r = f'border-right: 1px solid {_ts.TABLE_ROW_SEP};'
                else:
                    border_r = ''
                kleur = _ts.TABLE_LABEL_COLOR if is_naam else _ts.TABLE_VALUE_COLOR
                lbl.setStyleSheet(
                    f'font-family: {_ts.TABLE_FONT}; font-size: 12px; color: {kleur}; '
                    f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
                )
                grid.addWidget(lbl, data_start + i, col)

    def _laag_rijen(
        self,
        profiel: SoilProfile | None,
    ) -> list[list[str]]:
        """Geef rijen [naam, bk, ok] per laag voor een profiel.

        Parameters
        ----------
        profiel : SoilProfile | None
            Het grondprofiel, of None als het niet gevonden is.

        Returns
        -------
        list[list[str]]
            Lijst van [laagnaam, b.k. niveau, o.k. niveau] per laag.
        """
        if not profiel:
            return []
        n = len(profiel.layers)
        rijen = []
        for i, laag in enumerate(profiel.layers):
            bk = fmt_number(laag.level, 2)
            ok = fmt_number(profiel.layers[i + 1].level, 2) if i + 1 < n else 'Max'
            rijen.append([laag.material, bk, ok])
        return rijen
