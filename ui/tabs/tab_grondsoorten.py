"""Tab Grondsoortentabel — toont grondparameters voor alle profielen."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt

from parsers.models import Project, SoilProfile
from ui.table_styles import (
    TABLE_BORDER, TABLE_FONT, TABLE_HEADER_BG, TABLE_HEADER_FG,
    TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG, TABLE_LABEL_COLOR,
    TABLE_ROW_EVEN_BG, TABLE_ROW_ODD_BG, TABLE_ROW_SEP, TABLE_VALUE_COLOR,
)
from utils.formatting import fmt_number

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

_COL_STRETCH: list[int] = [14, 14, 20, 14, 14, 14, 14, 14, 14, 14, 14]

_KOLOMMEN: list[tuple[str, str]] = [
    ('BK laag\n[m NAP]',   'bk'),
    ('OK laag\n[m NAP]',   'ok'),
    ('Laag',               'naam'),
    ('γd\n[kN/m³]',        'gd'),
    ('γn\n[kN/m³]',        'gn'),
    ("c'kar\n[kN/m²]",     'c'),
    ("φ'kar\n[°]",         'phi'),
    ('δ\n[°]',             'delta'),
    ('kh1',                'kh1'),
    ('kh2',                'kh2'),
    ('kh3',                'kh3'),
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
        """Render alle grondsoortentabellen onder elkaar.

        Parameters
        ----------
        project : Project | None
            Het actieve project, of None om de tab leeg te tonen.
        """
        self._project = project
        self._clear_content()

        if not project or not project.profiles:
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
            rijen.append([
                fmt_number(bk, 2),
                ok_val,
                laag.material,
                fmt_number(soil.gamma_dry) if soil else '-',
                fmt_number(soil.gamma_wet) if soil else '-',
                fmt_number(soil.cohesion)  if soil else '-',
                fmt_number(soil.phi)       if soil else '-',
                fmt_number(soil.delta)     if soil else '-',
                str(int(soil.kh1)) if soil and soil.kh1 else '-',
                str(int(soil.kh2)) if soil and soil.kh2 else '-',
                str(int(soil.kh3)) if soil and soil.kh3 else '-',
            ])
        return rijen

    def _maak_kolomhoofden(self) -> QWidget:
        """Maak de headerrij met kolomlabels.

        Returns
        -------
        QWidget
            Widget met gestijlde kolomkoppen in een grid.
        """
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_SUBHDR_BG};')
        grid = QGridLayout(hdr)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        for col, (tekst, _) in enumerate(_KOLOMMEN):
            lbl = QLabel(tekst)
            kop_uitlijning = Qt.AlignmentFlag.AlignLeft if col == 2 else Qt.AlignmentFlag.AlignCenter
            lbl.setAlignment(kop_uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if col < len(_KOLOMMEN) - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 5px 8px; text-transform: uppercase; {border_r}'
            )
            grid.addWidget(lbl, 0, col)
            grid.setColumnStretch(col, _COL_STRETCH[col])

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
                Qt.AlignmentFlag.AlignLeft if col == 2
                else Qt.AlignmentFlag.AlignCenter
            )
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < len(waarden) - 1 else ''
            kleur = _LABEL_CLR if col == 2 else _VALUE_CLR
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
