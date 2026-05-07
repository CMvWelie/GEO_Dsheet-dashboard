"""Tab 2B — Invoerbeschrijving: dynamische lijst per fase."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QHBoxLayout, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor

from reporting.builders.damwand_tekst import (
    FASERING_INTRO_TEKST,
    FASERING_TABEL_INTRO_TEKST,
    FASERING_TITEL,
    faseringsregels,
)
from reporting.builders.input_description_builder import FaseCard, DamwandCard
from ui.table_styles import (
    TABLE_BORDER, TABLE_EXTRA_COLOR, TABLE_FONT, TABLE_HEADER_BG,
    TABLE_HEADER_FG, TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG,
    TABLE_LABEL_COLOR, TABLE_ROW_EVEN_BG, TABLE_ROW_ODD_BG, TABLE_ROW_SEP,
    TABLE_HEADER_SIZE, TABLE_TEXT_SIZE, TABLE_VALUE_COLOR,
)

# ── Kleurconstanten ──────────────────────────────────────────────────────────
_HDR_BG        = TABLE_HEADER_BG
_HDR_FG        = TABLE_HEADER_FG
_SUBHDR_BG     = TABLE_HEADER_SUB_BG
_SUBHDR_FG     = TABLE_HEADER_SUB_FG
_BORDER        = TABLE_BORDER
_ROW_SEP       = TABLE_ROW_SEP
_ROW_ODD_BG    = TABLE_ROW_ODD_BG
_ROW_EVEN_BG   = TABLE_ROW_EVEN_BG
_LABEL_CLR     = TABLE_LABEL_COLOR
_VALUE_CLR     = TABLE_VALUE_COLOR
_EXTRA_CLR     = TABLE_EXTRA_COLOR
_CARD_BG       = '#ffffff'
_SCROLL_BG     = '#e8eef3'
_IMG_BORDER    = '#d0dde8'
_IMG_BG        = '#f8fbfd'

# ── Typografie ────────────────────────────────────────────────────────────────
_FONT          = TABLE_FONT
_HDR_PT        = TABLE_HEADER_SIZE
_DATA_PT       = TABLE_TEXT_SIZE
_TEXT_STRETCH  = 100
_IMG_STRETCH   = 63
_PARAM_STRETCH = 3
_NIVEAU_STRETCH = 2
_TOEL_STRETCH  = 5
_ROW_HEIGHT_PX = 17
_DAMWAND_SPACING_PX = max(1, _ROW_HEIGHT_PX // 5)
_DAMWAND_DATA_MIN_HEIGHT_PX = 27
_IMG_RENDER_W  = 360
_IMG_RENDER_H  = 800


class TabInputDesc(QWidget):
    """Toont een fase-kaart per stage met vaste rijen (Tab 2B)."""

    override_changed = pyqtSignal(str, str)  # backwards-compat

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._damwand_widget: QWidget | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(20)
        self._layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate_fase_cards(
        self,
        cards: list[FaseCard],
        fase_namen: list[str] | None = None,
    ) -> None:
        """Vervang de inhoud door een kaart per fase."""
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cards:
            lbl = QLabel('Geen fases beschikbaar. Laad een project.')
            lbl.setStyleSheet(
                f'color: #7a93a8; font-size: 13px; font-family: {_FONT}; '
                f'padding: 32px 20px;'
            )
            self._layout.insertWidget(0, lbl)
            return

        self._layout.insertWidget(
            self._layout.count() - 1,
            self._maak_fasering_intro(cards, fase_namen),
        )
        for card in cards:
            self._layout.insertWidget(self._layout.count() - 1,
                                       self._make_card(card))

    def populate_damwand_card(self, card: DamwandCard | None) -> None:
        """Toon of verberg de damwandkaart bovenaan de tab."""
        if hasattr(self, '_damwand_widget') and self._damwand_widget is not None:
            self._damwand_widget.deleteLater()
            self._damwand_widget = None

        if card is None:
            return

        self._damwand_widget = self._maak_damwand_card(card)
        # Invoegen op positie 0 (vóór de fase-kaarten en de stretch)
        self._layout.insertWidget(0, self._damwand_widget)

    # ------------------------------------------------------------------
    # Kaart-opbouw
    # ------------------------------------------------------------------

    def _make_card(self, card: FaseCard) -> QWidget:
        # Wrapper voor schaduweffect — QGraphicsEffect op QFrame met children kan
        # artefacten geven; gebruik een QWidget als buitenste container.
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(27, 58, 92, 45))
        wrapper.setGraphicsEffect(shadow)

        outer_layout = QVBoxLayout(wrapper)
        outer_layout.setContentsMargins(4, 4, 4, 6)   # ruimte voor schaduw
        outer_layout.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: {_CARD_BG}; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        outer_layout.addWidget(frame)

        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ── 1. Header-balk (fasennaam | "Afbeelding") ─────────────────
        hdr = self._make_header(card.stage_name)
        card_layout.addWidget(hdr)

        # ── 2. Kolomhoofden (Parameter | Niveau | Toelichting) ─────────
        col_hdr = self._make_column_header()
        card_layout.addWidget(col_hdr)

        # ── 3. Body: datagrid + afbeelding ───────────────────────────
        body = self._make_body(card)
        card_layout.addWidget(body)

        return wrapper

    def _maak_damwand_card(self, card: DamwandCard) -> QWidget:
        """Bouw de vaste damwandkaart als tabel bovenaan de tab."""
        from utils.formatting import fmt_number

        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(27, 58, 92, 45))
        wrapper.setGraphicsEffect(shadow)

        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(4, 4, 4, 6)
        outer.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(
            f'QFrame {{ background: {_CARD_BG}; border: none; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        outer.addWidget(frame)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 8, 0, 10)
        lay.setSpacing(0)

        titel = QLabel('Damwandgegevens')
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
            f'color: {_LABEL_CLR}; background: transparent; padding: 0 0 6px 0; '
            f'border: none;'
        )
        lay.addWidget(titel)

        intro = QLabel(card.intro_tekst)
        intro.setWordWrap(True)
        intro.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_LABEL_CLR}; '
            f'background: transparent; padding: 0 0 8px 0; border: none;'
        )
        lay.addWidget(intro)

        rijen: list[tuple[str, str, str] | None] = [
            ('Profiel', card.profiel, '[-]'),
            ('Staalkwaliteit', card.staalkwaliteit, '[-]'),
            ('Hoogte', fmt_number(card.hoogte_mm), '[mm]'),
            ('Breedte', fmt_number(card.breedte_mm), '[mm]'),
            ('Buigstijfheid EI', fmt_number(card.ei_knm2), '[kNm²/m]'),
            ('Weerstandsmoment Wy;el', fmt_number(card.weerstandsmoment_cm3), '[cm³/m]'),
            ('Opneembaar moment M', fmt_number(card.opneembaar_moment_knm), '[kNm/m]'),
            ('Kopniveau', fmt_number(card.kopniveau), '[m NAP]'),
            ('Teenniveau', fmt_number(card.teenniveau), '[m NAP]'),
            ('Lengte', fmt_number(card.lengte), '[m]'),
        ]
        if card.ondersteuningen:
            rijen.append(None)
            for naam, niveau in card.ondersteuningen:
                rijen.append((naam, fmt_number(niveau), '[m NAP]'))

        grid_w = QWidget()
        grid_w.setStyleSheet(f'background: {_CARD_BG}; border: none;')
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnStretch(0, 5)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)

        for col, tekst in enumerate(['Parameter', 'Waarde', 'Eenheid']):
            header = QLabel(tekst)
            header.setMinimumHeight(_DAMWAND_DATA_MIN_HEIGHT_PX)
            border_l = f'border-left: 1px solid {_BORDER};' if col == 0 else ''
            border_r = f'border-right: 1px solid {_BORDER};'
            header.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 3px 6px; '
                f'min-height: {_DAMWAND_DATA_MIN_HEIGHT_PX}px; {border_l} '
                f'border-top: 1px solid {_BORDER}; {border_r} '
            )
            grid.addWidget(header, 0, col)

        aantal_data_rijen = sum(1 for rij in rijen if rij is not None)
        data_index = 0
        grid_row = 1
        for rij_index, rij in enumerate(rijen):
            if rij is None:
                spacing = QLabel('')
                spacing.setFixedHeight(_DAMWAND_SPACING_PX)
                spacing.setStyleSheet(f'background: {_CARD_BG}; padding: 0; border: none;')
                grid.addWidget(spacing, grid_row, 0, 1, 3)
                grid_row += 1
                continue

            label, waarde, eenheid = rij
            bg = _ROW_ODD_BG if data_index % 2 == 0 else _ROW_EVEN_BG
            gevolgd_door_spacing = (
                rij_index + 1 < len(rijen) and rijen[rij_index + 1] is None
            )
            border_t = f'border-top: 1px solid {_ROW_SEP};'
            border_b = f'border-bottom: 1px solid {_ROW_SEP};' if gevolgd_door_spacing else ''

            lbl = QLabel(label)
            lbl.setMinimumHeight(_DAMWAND_DATA_MIN_HEIGHT_PX)
            label_border_l = f'border-left: 1px solid {_ROW_SEP};'
            label_border_r = f'border-right: 1px solid {_ROW_SEP};'
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-weight: 400; '
                f'color: {_LABEL_CLR}; background: {bg}; padding: 2px 6px; '
                f'min-height: {_DAMWAND_DATA_MIN_HEIGHT_PX}px; '
                f'{label_border_l} {label_border_r} {border_t} {border_b}'
            )
            val = QLabel(waarde)
            val.setMinimumHeight(_DAMWAND_DATA_MIN_HEIGHT_PX)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            waarde_border_r = f'border-right: 1px solid {_ROW_SEP};'
            val.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_VALUE_CLR}; '
                f'background: {bg}; padding: 2px 6px; min-height: {_DAMWAND_DATA_MIN_HEIGHT_PX}px; '
                f'{waarde_border_r} {border_t} {border_b}'
            )
            ext = QLabel(eenheid)
            ext.setMinimumHeight(_DAMWAND_DATA_MIN_HEIGHT_PX)
            eenheid_border_r = f'border-right: 1px solid {_ROW_SEP};'
            ext.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-style: italic; '
                f'color: {_EXTRA_CLR}; background: {bg}; padding: 2px 6px; '
                f'min-height: {_DAMWAND_DATA_MIN_HEIGHT_PX}px; {eenheid_border_r} {border_t} {border_b}'
            )
            grid.addWidget(lbl, grid_row, 0)
            grid.addWidget(val, grid_row, 1)
            grid.addWidget(ext, grid_row, 2)
            grid_row += 1
            data_index += 1

        for col in range(3):
            sluitlijn = QLabel('')
            sluitlijn.setFixedHeight(1)
            sluitlijn.setStyleSheet(f'background: {_ROW_SEP}; padding: 0; border: none;')
            grid.addWidget(sluitlijn, grid_row, col)

        tabel_rij = QWidget()
        tabel_rij_layout = QHBoxLayout(tabel_rij)
        tabel_rij_layout.setContentsMargins(0, 0, 0, 0)
        tabel_rij_layout.setSpacing(0)
        tabel_rij_layout.addWidget(grid_w, stretch=16)
        tabel_rij_layout.addStretch(10)
        lay.addWidget(tabel_rij)

        toelichting = QLabel(
            'Hierin is:\n' + '\n'.join(
                f'{symbool}\t{omschrijving}'
                for symbool, omschrijving in card.toelichting_regels
            )
        )
        toelichting.setWordWrap(True)
        toelichting.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_LABEL_CLR}; '
            f'background: transparent; padding: 8px 0 0 0; border: none;'
        )
        lay.addWidget(toelichting)
        return wrapper

    def _maak_fasering_intro(
        self,
        cards: list[FaseCard],
        fase_namen: list[str] | None = None,
    ) -> QWidget:
        """Bouw de tekstuele inleiding voor de fasering."""
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: {_CARD_BG}; border: none; }}')

        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(4, 0, 4, 0)
        outer.setSpacing(0)
        outer.addWidget(frame)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        titel = QLabel(FASERING_TITEL)
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
            f'color: {_LABEL_CLR}; background: transparent; padding: 0 0 4px 0; '
            f'border: none;'
        )
        lay.addWidget(titel)

        intro = QLabel(FASERING_INTRO_TEKST)
        intro.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_LABEL_CLR}; '
            f'background: transparent; border: none;'
        )
        lay.addWidget(intro)

        namen = fase_namen or [card.stage_name for card in cards]
        for regel in faseringsregels(namen):
            fase = QLabel(f'•  {regel}')
            fase.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_LABEL_CLR}; '
                f'background: transparent; border: none; padding-left: 12px;'
            )
            lay.addWidget(fase)

        tabel_intro = QLabel(FASERING_TABEL_INTRO_TEKST)
        tabel_intro.setWordWrap(True)
        tabel_intro.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_LABEL_CLR}; '
            f'background: transparent; border: none; padding: 4px 0 0 0;'
        )
        lay.addWidget(tabel_intro)
        return wrapper

    def _make_header(self, stage_name: str) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_HDR_BG};')
        layout = QHBoxLayout(hdr)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Fase-naam
        naam_lbl = QLabel(stage_name)
        naam_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        naam_lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 3px 6px; '
            f'min-height: 17px;'
        )
        layout.addWidget(naam_lbl, stretch=_TEXT_STRETCH)

        # Scheidingslijn + afbeelding-header
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet('color: rgba(255,255,255,50); background: rgba(255,255,255,50);')
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        img_lbl = QLabel('Afbeelding')
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        img_lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 3px 6px; '
            f'min-height: 17px;'
        )
        layout.addWidget(img_lbl, stretch=_IMG_STRETCH)

        return hdr

    def _make_column_header(self) -> QWidget:
        col_hdr = QWidget()
        col_hdr.setStyleSheet(
            f'background: {_SUBHDR_BG}; border-top: none; border-bottom: 1px solid {_BORDER};'
        )
        layout = QHBoxLayout(col_hdr)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Datagrid kolomhoofden
        data_hdr = QWidget()
        data_hdr.setStyleSheet(f'background: {_SUBHDR_BG};')
        data_grid = QGridLayout(data_hdr)
        data_grid.setContentsMargins(0, 0, 0, 0)
        data_grid.setSpacing(0)
        data_grid.setColumnStretch(0, _PARAM_STRETCH)
        data_grid.setColumnStretch(1, _NIVEAU_STRETCH)
        data_grid.setColumnStretch(2, _TOEL_STRETCH)

        col_defs: list[tuple[str, Qt.AlignmentFlag]] = [
            ('Parameter',   Qt.AlignmentFlag.AlignLeft),
            ('Niveau',      Qt.AlignmentFlag.AlignRight),
            ('Toelichting', Qt.AlignmentFlag.AlignLeft),
        ]
        for i, (tekst, uitlijning) in enumerate(col_defs):
            lbl = QLabel(tekst)
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if i < 2 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 3px 6px; letter-spacing: 0; min-height: 17px; '
                f'{border_r}'
            )
            data_grid.addWidget(lbl, 0, i)

        layout.addWidget(data_hdr, stretch=_TEXT_STRETCH)

        # Spacer voor afbeelding-kolom
        spacer = QLabel()
        spacer.setStyleSheet(
            f'background: {_SUBHDR_BG}; border-left: 1px solid {_BORDER};'
        )
        layout.addWidget(spacer, stretch=_IMG_STRETCH)

        return col_hdr

    def _make_body(self, card: FaseCard) -> QWidget:
        body = QWidget()
        body.setStyleSheet(f'background: {_CARD_BG};')
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── Datagrid ──────────────────────────────────────────────────
        grid_widget = QWidget()
        grid_widget.setStyleSheet('background: transparent;')
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnStretch(0, _PARAM_STRETCH)
        grid.setColumnStretch(1, _NIVEAU_STRETCH)
        grid.setColumnStretch(2, _TOEL_STRETCH)

        grid_row = 0
        for row_i, row in enumerate(card.rows):
            n_sub = 1 + len(row.extra_lines)
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVEN_BG
            is_last_group = row_i == len(card.rows) - 1
            border_b = '' if is_last_group else f'border-bottom: 1px solid {_ROW_SEP};'

            lbl = QLabel(row.label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-weight: 400; '
                f'color: {_LABEL_CLR}; background: {bg}; '
                f'padding: 2px 6px; min-height: 13px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )

            val = QLabel(row.value)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            val.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-weight: 400; '
                f'color: {_VALUE_CLR}; background: {bg}; '
                f'padding: 2px 6px; min-height: 13px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )

            grid.addWidget(lbl, grid_row, 0, n_sub, 1)
            grid.addWidget(val, grid_row, 1, n_sub, 1)

            for k, tekst in enumerate([row.extra] + row.extra_lines):
                is_last_sub = k == n_sub - 1
                sub_border = '' if (not is_last_sub or is_last_group) else (
                    f'border-bottom: 1px solid {_ROW_SEP};'
                )
                extra = QLabel(tekst)
                extra.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                extra.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-weight: 400; '
                    f'color: {_EXTRA_CLR}; background: {bg}; '
                    f'padding: 2px 6px; min-height: 13px; {sub_border}'
                )
                grid.addWidget(extra, grid_row + k, 2)

            grid_row += n_sub

        padding_hoogte = self._padding_hoogte_px(card, grid_row)
        if padding_hoogte > 0:
            padding = QLabel('')
            padding.setMinimumHeight(padding_hoogte)
            padding.setStyleSheet(
                f'background: {_CARD_BG}; border-right: 1px solid {_ROW_SEP};'
            )
            grid.addWidget(padding, grid_row, 0, 1, 3)

        body_layout.addWidget(grid_widget, stretch=_TEXT_STRETCH)

        # ── Afbeeldingscontainer ──────────────────────────────────────
        img_container = QWidget()
        img_container.setStyleSheet(
            f'background: {_IMG_BG}; border-left: 1px solid {_IMG_BORDER};'
        )
        img_vbox = QVBoxLayout(img_container)
        img_vbox.setContentsMargins(6, 6, 6, 6)
        img_vbox.setSpacing(0)
        img_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if card.image_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(card.image_bytes)
            scaled = pixmap.scaled(
                _IMG_RENDER_W,
                _IMG_RENDER_H,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            img_lbl = QLabel()
            img_lbl.setPixmap(scaled)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet('background: transparent; border: none;')
            img_vbox.addWidget(img_lbl)
        else:
            img_vbox.addStretch()
            placeholder = QLabel('Geen afbeelding\nbeschikbaar')
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(
                f'color: #9cb3c6; font-size: {_DATA_PT}pt; font-style: italic; '
                f'font-family: {_FONT}; background: transparent; border: none;'
            )
            img_vbox.addWidget(placeholder)
            img_vbox.addStretch()

        body_layout.addWidget(img_container, stretch=_IMG_STRETCH)

        return body

    def _padding_hoogte_px(self, card: FaseCard, gevulde_rijen: int) -> int:
        """Geef extra lege teksthoogte als de afbeelding hoger is dan de tekstzijde."""
        if not card.image_bytes or gevulde_rijen <= 0:
            return 0

        pixmap = QPixmap()
        if not pixmap.loadFromData(card.image_bytes):
            return 0

        scaled = pixmap.scaled(
            _IMG_RENDER_W,
            _IMG_RENDER_H,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        teksthoogte = gevulde_rijen * _ROW_HEIGHT_PX
        return max(0, scaled.height() - teksthoogte)
