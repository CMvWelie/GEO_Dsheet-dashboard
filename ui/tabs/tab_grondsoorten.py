"""Tab Grondsoortentabel — toont grondparameters voor alle profielen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt

from parsers.models import Project, SoilProfile, Stage
from ui.table_styles import (
    TABLE_BORDER, TABLE_FONT, TABLE_HEADER_BG, TABLE_HEADER_FG,
    TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG, TABLE_LABEL_COLOR,
    TABLE_ROW_EVEN_BG, TABLE_ROW_ODD_BG, TABLE_ROW_SEP, TABLE_VALUE_COLOR,
)
from utils.formatting import fmt_number
import ui.table_styles as _ts

# ── Kleurconstanten (zelfde palet als tab_input_desc) ───────────────────────
_HDR_BG     = TABLE_HEADER_BG
_HDR_FG     = TABLE_HEADER_FG
_SUBHDR_BG  = TABLE_HEADER_SUB_BG
_SUBHDR_FG  = TABLE_HEADER_SUB_FG
_BORDER     = TABLE_BORDER
_ROW_SEP    = TABLE_ROW_SEP
_ROW_ODD_BG = TABLE_ROW_ODD_BG
_ROW_EVN_BG = TABLE_ROW_EVEN_BG
_LABEL_CLR  = TABLE_LABEL_COLOR
_VALUE_CLR  = TABLE_VALUE_COLOR
_FONT       = TABLE_FONT

def _laag_sleutels(profiel: SoilProfile | None) -> list[tuple[float, str]]:
    """Vergelijkbare sleutel per laag: (level, material)."""
    if not profiel:
        return []
    return [(laag.level, laag.material) for laag in profiel.layers]


def _find_profiel(profielen: list[SoilProfile], naam: str) -> SoilProfile | None:
    return next((p for p in (profielen or []) if p.name == naam), None)


def _fase_intro(namen: list[str]) -> tuple[str, list[str]]:
    """Bouw de introtekst en eventuele faselijst voor een grondlaagopbouw."""
    if len(namen) == 1:
        return f'In de fase "{namen[0]}" wordt het volgende profiel gehanteerd:', []
    return 'Het volgende profiel wordt gehanteerd in de volgende fases:', namen


def _is_enkelvoudig(project: Project) -> bool:
    """True als alle fases dezelfde L=R profielopbouw hebben."""
    if not project.stages:
        return True
    prof_map = {p.name: p for p in project.profiles}
    referentie: tuple | None = None
    for fase in project.stages:
        sl = tuple(_laag_sleutels(prof_map.get(fase.left_profile)))
        sr = tuple(_laag_sleutels(prof_map.get(fase.right_profile)))
        if sl != sr:
            return False
        if referentie is None:
            referentie = sl
        elif sl != referentie:
            return False
    return True


_COL_STRETCH: list[int] = [37, 15, 15, 15, 14, 14, 14, 13, 13, 13]

_KOLOMMEN: list[tuple[str, str]] = [
    ('Laag',        'naam'),
    ('BK laag',     'bk'),
    ('OK laag',     'ok'),
    ('Γd / yn',     'gd_gn'),
    ("c'kar",       'c'),
    ("φ'kar",       'phi'),
    ('δ',           'delta'),
    ('kh1',         'kh1'),
    ('kh2',         'kh2'),
    ('kh3',         'kh3'),
]

_EENHEDEN_RIJ: list[tuple[str, int]] = [
    ('', 1),              # Laag
    ('[m NAP]', 2),       # BK laag + OK laag
    ('[kN/m³]', 1),       # Γd / yn
    ('[kN/m²]', 1),       # c'kar
    ('[°]', 2),           # φ'kar + δ
    ('[kN/m³]', 3),       # kh1 + kh2 + kh3
]

_FASE_COL_STRETCH = [4, 2, 2, 4, 2, 2]
_FASE_COL_STRETCH_ENKEL = [4, 2, 2]

_SOIL_COL_STRETCH = [30, 12, 10, 10, 10, 10, 9, 9]

_SOIL_KOLOMMEN: list[str] = [
    'Laag',
    'Γd / yn',
    "c'kar",
    "φ'kar",
    'δ',
    'kh1',
    'kh2',
    'kh3',
]

_SOIL_EENHEDEN_RIJ: list[tuple[str, int]] = [
    ('', 1),          # Laag
    ('[kN/m³]', 1),   # Γd / yn
    ('[kN/m²]', 1),   # c'kar
    ('[°]', 2),       # φ'kar + δ
    ('[kN/m³]', 3),   # kh1 + kh2 + kh3
]

_SOIL_COL_STRETCH_MET_NIVEAU = [22, 8, 8, 10, 10, 8, 8, 8, 7, 7]

_SOIL_KOLOMMEN_MET_NIVEAU: list[str] = [
    'Laag',
    'BK laag',
    'OK laag',
    'Γd / yn',
    "c'kar",
    "φ'kar",
    'δ',
    'kh1',
    'kh2',
    'kh3',
]

_SOIL_EENHEDEN_RIJ_MET_NIVEAU: list[tuple[str, int]] = [
    ('', 1),          # Laag
    ('[m NAP]', 2),   # BK laag + OK laag
    ('[kN/m³]', 1),   # Γd / yn
    ('[kN/m²]', 1),   # c'kar
    ('[°]', 2),       # φ'kar + δ
    ('[kN/m³]', 3),   # kh1 + kh2 + kh3
]


class TabGrondsoorten(QWidget):
    """Toont grondparameters per profiel onder elkaar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ── Scrollgebied ─────────────────────────────────────────────────
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
        """Render grondsoortentabel op basis van projectconfiguratie.

        Parameters
        ----------
        project : Project | None
            Het actieve project, of None om de tab leeg te tonen.
        """
        self._project = project
        self._clear_content()

        if not project:
            self._render_leeg()
            return

        if _is_enkelvoudig(project) and not project.stages:
            self._render_enkelvoudig(project)
        else:
            self._render_volledig(project)

    def _render_enkelvoudig(self, project: Project) -> None:
        """Toon profieltabellen met grondparameters (enkelvoudig pad)."""
        if not project.profiles:
            self._render_leeg()
            return

        intro = self._maak_intro_tekst()
        self._content_layout.insertWidget(self._content_layout.count() - 1, intro)

        soil_map = {s.name: s for s in project.soils}
        referentie_titel = ''
        referentie_rijen: list[list[str]] = []
        for nummer, profiel in enumerate(project.profiles, start=1):
            profiel_titel = f'{nummer}* — {profiel.name}'
            kop = self._maak_profiel_kop(nummer, profiel.name)
            self._content_layout.insertWidget(self._content_layout.count() - 1, kop)
            tabel = self._maak_tabel(profiel, soil_map, referentie_rijen, referentie_titel)
            self._content_layout.insertWidget(self._content_layout.count() - 1, tabel)
            if nummer == 1:
                referentie_titel = profiel_titel
                referentie_rijen = self._maak_rij_waarden(profiel, soil_map)

    def _render_volledig(self, project: Project) -> None:
        """Toon grondsoortenoverzicht en per-fase grondlaagentabellen (volledig pad)."""
        if not project.soils:
            self._render_leeg()
            return

        prof_map = {pr.name: pr for pr in project.profiles}
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

        if len(groepen) == 1:
            groep = groepen[0]
            links_rijen = self._laag_rijen(prof_map.get(groep['fase_ref'].left_profile))
            rechts_rijen = self._laag_rijen(prof_map.get(groep['fase_ref'].right_profile))
            if bool(links_rijen) and links_rijen == rechts_rijen:
                profiel = prof_map.get(groep['fase_ref'].left_profile)
                self._voeg_sectie_kop_toe('Grondsoorten')
                self._voeg_fase_intro_toe(groep['namen'], witregel_na=True)
                self._content_layout.insertWidget(
                    self._content_layout.count() - 1,
                    self._maak_grondsoorten_tabel(project, profiel=profiel),
                )
                return

        self._voeg_sectie_kop_toe('Grondsoorten')
        self._content_layout.insertWidget(
            self._content_layout.count() - 1,
            self._maak_grondsoorten_tabel(project),
        )

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

    def _render_leeg(self) -> None:
        """Toon een lege-state bericht wanneer er geen profieldata is."""
        lbl = QLabel('Geen profieldata beschikbaar. Laad een project.')
        lbl.setStyleSheet(
            f'color: #7a93a8; font-size: 13px; font-family: {_FONT}; padding: 32px 20px;'
        )
        self._content_layout.insertWidget(0, lbl)

    def _clear_content(self) -> None:
        """Verwijder alle widgets uit het scrollgebied, behalve de stretch."""
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ------------------------------------------------------------------
    # Tabelopbouw
    # ------------------------------------------------------------------

    def _maak_intro_tekst(self) -> QWidget:
        """Toelichting boven de grondsoortentabel."""
        tekst = (
            'In de onderstaande tabel zijn de sterkteparameters opgenomen die meegenomen zijn '
            'in de toetsing en dimensionering van de damwand. De grondopbouw en bijbehorende '
            'grondparameters zijn bepaald met behulp van NEN-EN\u00a01997-1:2025/NB '
            'tabel\u00a02.b karakteristieke waarde van grondeigenschappen.'
        )
        lbl = QLabel(tekst)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 12px; color: {_LABEL_CLR}; '
            f'background: transparent; padding: 0px 4px 12px 4px;'
        )
        return lbl

    def _maak_profiel_kop(self, nummer: int, naam: str) -> QWidget:
        """Maak een sectiekop voor een profiel."""
        lbl = QLabel(f'{nummer}* — {naam}')
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 13px; font-weight: 600; '
            f'color: {_LABEL_CLR}; background: transparent; '
            f'padding: 16px 4px 6px 4px;'
        )
        return lbl

    def _maak_tabel(
        self,
        profiel: SoilProfile,
        soil_map: dict,
        referentie_rijen: list[list[str]] | None = None,
        referentie_titel: str = '',
    ) -> QWidget:
        """Maak een volledig gestijlde tabelframe voor één profiel.

        Parameters
        ----------
        profiel : SoilProfile
            Het te tonen grondprofiel.
        soil_map : dict
            Mapping van grondnaam naar Soil-object voor opzoeken parameters.

        Returns
        -------
        QWidget
            Frame met kolomhoofden en datarijen.
        """
        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Kolomhoofden
        layout.addWidget(self._maak_kolomhoofden())

        # Datarijen
        rijen = self._maak_rij_waarden(profiel, soil_map)
        n_lagen = len(profiel.layers)
        for i, rij_vals in enumerate(rijen):
            bg = _ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG
            is_last = i == n_lagen - 1

            if (
                referentie_titel
                and referentie_rijen
                and i < len(referentie_rijen)
                and rij_vals == referentie_rijen[i]
            ):
                layout.addWidget(
                    self._maak_samengevoegde_rij(
                        f'gelijk aan {referentie_titel}',
                        bg,
                        is_last,
                    )
                )
                continue

            layout.addWidget(self._maak_rij(rij_vals, bg, is_last))

        return frame

    def _maak_rij_waarden(self, profiel: SoilProfile, soil_map: dict) -> list[list[str]]:
        """Maak de zichtbare celwaarden per laag voor een profiel."""
        rijen = []
        n_lagen = len(profiel.layers)
        for i, laag in enumerate(profiel.layers):
            bk = laag.level
            if i + 1 < n_lagen:
                ok_val: str = fmt_number(profiel.layers[i + 1].level, 2)
            else:
                ok_val = 'Max'

            soil = soil_map.get(laag.material)
            if soil:
                gd_gn = f'{fmt_number(soil.gamma_dry)} / {fmt_number(soil.gamma_wet)}'
            else:
                gd_gn = '-'

            rijen.append([
                laag.material,
                fmt_number(bk, 2),
                ok_val,
                gd_gn,
                fmt_number(soil.cohesion) if soil else '-',
                fmt_number(soil.phi)      if soil else '-',
                fmt_number(soil.delta)    if soil else '-',
                str(int(soil.kh1)) if soil and soil.kh1 else '-',
                str(int(soil.kh2)) if soil and soil.kh2 else '-',
                str(int(soil.kh3)) if soil and soil.kh3 else '-',
            ])
        return rijen

    def _maak_kolomhoofden(self) -> QWidget:
        """Maak de 2-rij headerwidget: rij 0 = kolomnamen, rij 1 = eenheden.

        Returns
        -------
        QWidget
            Widget met kolomkoppen en eenhedenrij in een grid.
        """
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_SUBHDR_BG};')
        grid = QGridLayout(hdr)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        # ── Rij 0: kolomnamen ────────────────────────────────────────────────
        for col, (tekst, _) in enumerate(_KOLOMMEN):
            lbl = QLabel(tekst)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft
                if col == 0
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if col < len(_KOLOMMEN) - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 5px 8px; text-transform: uppercase; '
                f'border-bottom: 1px solid {_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col)
            grid.setColumnStretch(col, _COL_STRETCH[col])

        # ── Rij 1: eenheden (samengevoegde cellen) ───────────────────────────
        col_offset = 0
        n_groepen = len(_EENHEDEN_RIJ)
        for groep_idx, (tekst, colspan) in enumerate(_EENHEDEN_RIJ):
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            is_laatste = groep_idx == n_groepen - 1
            border_r = '' if is_laatste else f'border-right: 1px solid {_BORDER};'
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 3px 8px; {border_r}'
            )
            grid.addWidget(lbl, 1, col_offset, 1, colspan)
            col_offset += colspan

        return hdr

    def _maak_rij(self, waarden: list[str], bg: str, is_last: bool) -> QWidget:
        """Maak één datarij met de opgegeven celwaarden.

        Parameters
        ----------
        waarden : list[str]
            Celinhoud voor elke kolom, in volgorde van _KOLOMMEN.
        bg : str
            Achtergrondkleur (afwisselend per rij).
        is_last : bool
            True als dit de laatste rij is (geen onderste rand).

        Returns
        -------
        QWidget
            Widget met de rij als grid.
        """
        rij = QWidget()
        grid = QGridLayout(rij)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

        for col, waarde in enumerate(waarden):
            lbl = QLabel(waarde)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft if col == 0
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < len(waarden) - 1 else ''
            kleur = _LABEL_CLR if col == 0 else _VALUE_CLR
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {kleur}; '
                f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
            )
            grid.addWidget(lbl, 0, col)
            grid.setColumnStretch(col, _COL_STRETCH[col])

        return rij

    def _maak_samengevoegde_rij(self, tekst: str, bg: str, is_last: bool) -> QWidget:
        """Maak een datarij die alle kolommen overspant."""
        rij = QWidget()
        layout = QVBoxLayout(rij)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

        lbl = QLabel(tekst)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 12px; color: {_LABEL_CLR}; '
            f'background: {bg}; padding: 6px 8px; {border_b}'
        )
        layout.addWidget(lbl)
        return rij

    # ------------------------------------------------------------------
    # Volledig pad — grondsoortenoverzicht (deel 1)
    # ------------------------------------------------------------------

    def _gebruikte_grondnamen(self, project: Project) -> set[str]:
        namen: set[str] = set()
        for profiel in project.profiles:
            for laag in profiel.layers:
                namen.add(laag.material)
        return namen

    def _maak_grondsoorten_tabel(
        self, project: Project, profiel: SoilProfile | None = None
    ) -> QWidget:
        met_niveau = profiel is not None
        kolommen = _SOIL_KOLOMMEN_MET_NIVEAU if met_niveau else _SOIL_KOLOMMEN
        eenheden = _SOIL_EENHEDEN_RIJ_MET_NIVEAU if met_niveau else _SOIL_EENHEDEN_RIJ
        stretch = _SOIL_COL_STRETCH_MET_NIVEAU if met_niveau else _SOIL_COL_STRETCH

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {_ts.TABLE_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._maak_grondsoorten_header(kolommen, eenheden, stretch))

        if met_niveau:
            rijen = self._grondsoorten_rijen_met_niveau(project, profiel)
        else:
            gebruikte = self._gebruikte_grondnamen(project)
            soils = [s for s in project.soils if s.name in gebruikte]
            rijen = self._grondsoorten_rijen(soils)

        for i, waarden in enumerate(rijen):
            bg = _ts.TABLE_ROW_ODD_BG if i % 2 == 0 else _ts.TABLE_ROW_EVEN_BG
            is_last = i == len(rijen) - 1
            layout.addWidget(self._maak_grondsoorten_rij(waarden, bg, is_last, stretch))

        return frame

    def _grondsoorten_rijen(self, soils: list) -> list[list[str]]:
        rijen = []
        for soil in soils:
            kh1 = str(int(soil.kh1)) if soil.kh1 else '-'
            kh2 = str(int(soil.kh2)) if soil.kh2 else '-'
            kh3 = str(int(soil.kh3)) if soil.kh3 else '-'
            rijen.append([
                soil.name,
                f'{fmt_number(soil.gamma_dry)} / {fmt_number(soil.gamma_wet)}',
                fmt_number(soil.cohesion),
                fmt_number(soil.phi),
                fmt_number(soil.delta),
                kh1, kh2, kh3,
            ])
        return rijen

    def _grondsoorten_rijen_met_niveau(
        self, project: Project, profiel: SoilProfile
    ) -> list[list[str]]:
        soil_map = {s.name: s for s in project.soils}
        n = len(profiel.layers)
        rijen = []
        for i, laag in enumerate(profiel.layers):
            bk = fmt_number(laag.level, 2)
            ok = fmt_number(profiel.layers[i + 1].level, 2) if i + 1 < n else '-'
            soil = soil_map.get(laag.material)
            if soil:
                kh1 = str(int(soil.kh1)) if soil.kh1 else '-'
                kh2 = str(int(soil.kh2)) if soil.kh2 else '-'
                kh3 = str(int(soil.kh3)) if soil.kh3 else '-'
                rijen.append([
                    laag.material, bk, ok,
                    f'{fmt_number(soil.gamma_dry)} / {fmt_number(soil.gamma_wet)}',
                    fmt_number(soil.cohesion),
                    fmt_number(soil.phi),
                    fmt_number(soil.delta),
                    kh1, kh2, kh3,
                ])
            else:
                rijen.append([laag.material, bk, ok] + ['-'] * 7)
        return rijen

    def _maak_grondsoorten_header(
        self,
        kolommen: list[str],
        eenheden_rij: list[tuple[str, int]],
        stretch: list[int],
    ) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_ts.TABLE_HEADER_SUB_BG};')
        grid = QGridLayout(hdr)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n = len(kolommen)
        for col, tekst in enumerate(kolommen):
            lbl = QLabel(tekst)
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
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 5px 8px; border-bottom: 1px solid {_ts.TABLE_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col)
            grid.setColumnStretch(col, stretch[col])

        col_offset = 0
        n_groepen = len(eenheden_rij)
        for groep_idx, (tekst, colspan) in enumerate(eenheden_rij):
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            is_laatste = groep_idx == n_groepen - 1
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};'
                if not is_laatste else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 3px 8px; {border_r}'
            )
            grid.addWidget(lbl, 1, col_offset, 1, colspan)
            col_offset += colspan

        return hdr

    def _maak_grondsoorten_rij(
        self, waarden: list[str], bg: str, is_last: bool, stretch: list[int]
    ) -> QWidget:
        rij = QWidget()
        grid = QGridLayout(rij)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        border_b = '' if is_last else f'border-bottom: 1px solid {_ts.TABLE_ROW_SEP};'

        for col, waarde in enumerate(waarden):
            lbl = QLabel(waarde)
            uitlijning = (
                Qt.AlignmentFlag.AlignLeft if col == 0
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_ROW_SEP};'
                if col < len(waarden) - 1 else ''
            )
            kleur = _ts.TABLE_LABEL_COLOR if col == 0 else _ts.TABLE_VALUE_COLOR
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {kleur}; '
                f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
            )
            grid.addWidget(lbl, 0, col)
            if col < len(stretch):
                grid.setColumnStretch(col, stretch[col])

        return rij

    # ------------------------------------------------------------------
    # Volledig pad — faselagen-tabellen (deel 2)
    # ------------------------------------------------------------------

    def _voeg_sectie_kop_toe(self, naam: str) -> None:
        lbl = QLabel(naam)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 13px; font-weight: 600; '
            f'color: {_LABEL_CLR}; background: transparent; '
            f'padding: 16px 4px 6px 4px;'
        )
        self._content_layout.insertWidget(self._content_layout.count() - 1, lbl)

    def _voeg_witregel_toe(self) -> None:
        spacer = QWidget()
        spacer.setFixedHeight(8)
        self._content_layout.insertWidget(self._content_layout.count() - 1, spacer)

    def _voeg_fase_intro_toe(
        self,
        namen: list[str],
        *,
        witregel_na: bool = False,
    ) -> None:
        intro, bullets = _fase_intro(namen)

        lbl = QLabel(intro)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 12px; '
            f'color: {_VALUE_CLR}; background: transparent; '
            f'padding: 0 4px 4px 4px;'
        )
        self._content_layout.insertWidget(self._content_layout.count() - 1, lbl)

        for fase_naam in bullets:
            bullet = QLabel(f'- {fase_naam}')
            bullet.setWordWrap(True)
            bullet.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; '
                f'color: {_VALUE_CLR}; background: transparent; '
                f'padding: 0 4px 2px 20px;'
            )
            self._content_layout.insertWidget(
                self._content_layout.count() - 1,
                bullet,
            )
        if bullets or witregel_na:
            self._voeg_witregel_toe()

    def _laag_rijen(self, profiel: SoilProfile | None) -> list[list[str]]:
        if not profiel:
            return []
        n = len(profiel.layers)
        rijen = []
        for i, laag in enumerate(profiel.layers):
            bk = fmt_number(laag.level, 2)
            ok = fmt_number(profiel.layers[i + 1].level, 2) if i + 1 < n else 'Max'
            rijen.append([laag.material, bk, ok])
        return rijen

    def _maak_fase_tabel(
        self,
        fase: Stage,
        project: Project,
        links_ongewijzigd: bool = False,
        rechts_ongewijzigd: bool = False,
    ) -> QWidget:
        links_profiel = _find_profiel(project.profiles, fase.left_profile)
        rechts_profiel = _find_profiel(project.profiles, fase.right_profile)
        links_rijen = self._laag_rijen(links_profiel)
        rechts_rijen = self._laag_rijen(rechts_profiel)
        zijden_gelijk = bool(links_rijen) and links_rijen == rechts_rijen
        geheel_ongewijzigd = links_ongewijzigd and rechts_ongewijzigd

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
                grid, 2, n_data, links_rijen, geheel_ongewijzigd, col_offset=0, links=False,
            )
            return self._verpak_halve_breedte(frame)

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
                f'font-family: {_FONT}; font-size: 10px; font-weight: 700; '
                f'color: {_ts.TABLE_HEADER_FG}; background: {_ts.TABLE_HEADER_BG}; '
                f'padding: 5px 8px; border-bottom: 1px solid {_ts.TABLE_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col_start, 1, 3)

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
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_ts.TABLE_HEADER_SUB_FG}; background: {_ts.TABLE_HEADER_SUB_BG}; '
                f'padding: 5px 8px; {border_r}'
            )
            grid.addWidget(lbl, 1, col)

        self._vul_helft(grid, 2, n_data, links_rijen, links_ongewijzigd, col_offset=0, links=True)
        self._vul_helft(grid, 2, n_data, rechts_rijen, rechts_ongewijzigd, col_offset=3, links=False)

        return frame

    def _verpak_halve_breedte(self, tabel: QWidget) -> QWidget:
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
        for col_start, tekst in groepen:
            lbl = QLabel(tekst)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = (
                f'border-right: 1px solid {_ts.TABLE_BORDER};'
                if col_start + 3 < totaal_kolommen else ''
            )
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 700; '
                f'color: {_ts.TABLE_HEADER_FG}; background: {_ts.TABLE_HEADER_BG}; '
                f'padding: 5px 8px; border-bottom: 1px solid {_ts.TABLE_BORDER}; {border_r}'
            )
            grid.addWidget(lbl, 0, col_start, 1, 3)

    def _voeg_fase_tabel_subkoppen_toe(
        self,
        grid: QGridLayout,
        subkoppen: list[str],
    ) -> None:
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
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
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
        scheiding_r = (
            f'border-right: 1px solid {_ts.TABLE_BORDER};' if links else ''
        )

        if ongewijzigd:
            lbl = QLabel('Grondopbouw ongewijzigd t.o.v. vorige fase')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                f'color: {_LABEL_CLR}; background: {_ROW_EVN_BG}; '
                f'padding: 6px 8px; {scheiding_r}'
            )
            grid.addWidget(lbl, data_start, col_offset, n_data, 3)
            return

        for i in range(n_data):
            bg = _ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG
            border_b = (
                '' if i == n_data - 1
                else f'border-bottom: 1px solid {_ROW_SEP};'
            )
            rij = rijen[i] if i < len(rijen) else ['', '', '']
            for j, waarde in enumerate(rij):
                col = col_offset + j
                lbl = QLabel(waarde)
                is_naam = j == 0
                uitlijning = Qt.AlignmentFlag.AlignLeft if is_naam else Qt.AlignmentFlag.AlignCenter
                lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                if links and j == 2:
                    border_r = scheiding_r
                elif j < 2:
                    border_r = f'border-right: 1px solid {_ROW_SEP};'
                else:
                    border_r = ''
                kleur = _LABEL_CLR if is_naam else _VALUE_CLR
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {kleur}; '
                    f'background: {bg}; padding: 6px 8px; {border_r} {border_b}'
                )
                grid.addWidget(lbl, data_start + i, col)
