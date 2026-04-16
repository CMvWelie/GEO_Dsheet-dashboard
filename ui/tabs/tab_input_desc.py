"""Tab 2B — Invoerbeschrijving: dynamische lijst per fase."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame,
    QLabel, QGridLayout, QHBoxLayout, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor

from reporting.builders.input_description_builder import FaseCard, DamwandCard

# ── Kleurconstanten ──────────────────────────────────────────────────────────
_HDR_BG        = '#1b3a5c'   # marine-blauw header
_HDR_FG        = '#ffffff'
_SUBHDR_BG     = '#274f77'   # iets lichter marine voor kolomhoofden
_SUBHDR_FG     = '#b8d4ea'
_BORDER        = '#c4d4e0'
_ROW_SEP       = '#dce8f0'
_ROW_ODD_BG    = '#f3f8fc'
_ROW_EVEN_BG   = '#ffffff'
_LABEL_CLR     = '#2c3f52'
_VALUE_CLR     = '#0f1e2b'
_EXTRA_CLR     = '#2171ae'
_CARD_BG       = '#ffffff'
_SCROLL_BG     = '#e8eef3'
_IMG_BORDER    = '#d0dde8'
_IMG_BG        = '#f8fbfd'
_IMG_W         = 500         # breedte afbeeldingskolom in pixels

# ── Typografie ────────────────────────────────────────────────────────────────
_FONT          = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'


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

    def populate_fase_cards(self, cards: list[FaseCard]) -> None:
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

        # ── 2. Kolomhoofden (Parameter | Waarde | Extra) ──────────────
        col_hdr = self._make_column_header()
        card_layout.addWidget(col_hdr)

        # ── 3. Body: datagrid + afbeelding ───────────────────────────
        body = self._make_body(card)
        card_layout.addWidget(body)

        return wrapper

    def _maak_damwand_card(self, card: DamwandCard) -> QWidget:
        """Bouw de vaste damwandkaart (bovenaan de tab)."""
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
            f'QFrame {{ background: {_CARD_BG}; border: 1px solid {_BORDER}; }}'
        )
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        outer.addWidget(frame)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setStyleSheet(f'background: {_HDR_BG};')
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        titel = QLabel('Damwandprofiel')
        titel.setStyleSheet(
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        hdr_lay.addWidget(titel)
        lay.addWidget(hdr)

        # Datarijen — None als schildwacht voor een horizontale deelstreep
        rijen: list[tuple[str, str, str] | None] = [
            ('Profiel',          card.profiel,                        ''),
            ('Staalkwaliteit',   card.staalkwaliteit,                 ''),
            ('Hoogte h',         fmt_number(card.hoogte_mm),          '[mm]'),
            ('Breedte b',        fmt_number(card.breedte_mm),         '[mm]'),
            ('E-modulus staal',  '2,10E+05',                          '[N/mm²]'),
            ('Kopniveau',        fmt_number(card.kopniveau),          '[m NAP]'),
            ('Teenniveau',       fmt_number(card.teenniveau),         '[m NAP]'),
            ('Lengte',           fmt_number(card.lengte),             '[m]'),
        ]
        if card.ondersteuningen:
            rijen.append(None)  # deelstreep
            for naam, niveau in card.ondersteuningen[:4]:
                rijen.append((naam, fmt_number(niveau), '[m NAP]'))

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnMinimumWidth(0, 190)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 120)

        n_data = sum(1 for r in rijen if r is not None)
        grid_row = 0
        data_index = 0
        for rij in rijen:
            if rij is None:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet(f'background: {_BORDER}; max-height: 2px; border: none;')
                grid.addWidget(sep, grid_row, 0, 1, 3)
                grid_row += 1
                continue

            label, waarde, eenheid = rij
            bg = _ROW_ODD_BG if data_index % 2 == 0 else _ROW_EVEN_BG
            is_last = data_index == n_data - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; font-weight: 500; '
                f'color: {_LABEL_CLR}; background: {bg}; padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            val = QLabel(waarde)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                f'background: {bg}; padding: 6px 14px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            ext = QLabel(eenheid)
            ext.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                f'color: {_EXTRA_CLR}; background: {bg}; padding: 6px 10px; {border_b}'
            )
            grid.addWidget(lbl, grid_row, 0)
            grid.addWidget(val, grid_row, 1)
            grid.addWidget(ext, grid_row, 2)
            grid_row += 1
            data_index += 1

        lay.addWidget(grid_w)
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
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        layout.addWidget(naam_lbl, stretch=1)

        # Scheidingslijn + afbeelding-header
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet('color: rgba(255,255,255,50); background: rgba(255,255,255,50);')
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        img_lbl = QLabel('Afbeelding')
        img_lbl.setFixedWidth(_IMG_W)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        img_lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 14px; font-weight: 700; '
            f'color: {_HDR_FG}; background: {_HDR_BG}; padding: 10px 16px;'
        )
        layout.addWidget(img_lbl)

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
        data_grid.setColumnMinimumWidth(0, 190)
        data_grid.setColumnStretch(1, 1)
        data_grid.setColumnMinimumWidth(2, 120)

        col_defs: list[tuple[str, Qt.AlignmentFlag]] = [
            ('Parameter',   Qt.AlignmentFlag.AlignLeft),
            ('Waarde',      Qt.AlignmentFlag.AlignRight),
            ('',            Qt.AlignmentFlag.AlignLeft),
        ]
        for i, (tekst, uitlijning) in enumerate(col_defs):
            lbl = QLabel(tekst)
            lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid #1d4568;' if i < 2 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_SUBHDR_BG}; '
                f'padding: 5px 12px; text-transform: uppercase; letter-spacing: 0.5px; '
                f'{border_r}'
            )
            data_grid.addWidget(lbl, 0, i)

        layout.addWidget(data_hdr, stretch=1)

        # Spacer voor afbeelding-kolom
        spacer = QLabel()
        spacer.setFixedWidth(_IMG_W)
        spacer.setStyleSheet(
            f'background: {_SUBHDR_BG}; border-left: 1px solid #1d4568;'
        )
        layout.addWidget(spacer)

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
        grid.setColumnMinimumWidth(0, 190)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 120)

        for row_i, row in enumerate(card.rows):
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVEN_BG
            is_last = row_i == len(card.rows) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'

            lbl = QLabel(row.label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; font-weight: 500; '
                f'color: {_LABEL_CLR}; background: {bg}; '
                f'padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )

            val = QLabel(row.value)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; font-weight: 400; '
                f'color: {_VALUE_CLR}; background: {bg}; '
                f'padding: 6px 14px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )

            extra = QLabel(row.extra)
            extra.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            extra.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                f'color: {_EXTRA_CLR}; background: {bg}; '
                f'padding: 6px 10px; {border_b}'
            )

            grid.addWidget(lbl,   row_i, 0)
            grid.addWidget(val,   row_i, 1)
            grid.addWidget(extra, row_i, 2)

        body_layout.addWidget(grid_widget, stretch=1)

        # ── Afbeeldingscontainer ──────────────────────────────────────
        img_container = QWidget()
        img_container.setFixedWidth(_IMG_W)
        img_container.setStyleSheet(
            f'background: {_IMG_BG}; border-left: 1px solid {_IMG_BORDER};'
        )
        img_vbox = QVBoxLayout(img_container)
        img_vbox.setContentsMargins(10, 10, 10, 10)
        img_vbox.setSpacing(0)
        img_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if card.image_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(card.image_bytes)
            scaled = pixmap.scaled(
                _IMG_W - 20,
                800,
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
                f'color: #9cb3c6; font-size: 12px; font-style: italic; '
                f'font-family: {_FONT}; background: transparent; border: none;'
            )
            img_vbox.addWidget(placeholder)
            img_vbox.addStretch()

        body_layout.addWidget(img_container)

        return body

