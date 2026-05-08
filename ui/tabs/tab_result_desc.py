"""Tab 3B — Resultaatbeschrijving: gegenereerde tekst + maatgevende resultaattabel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGroupBox, QGridLayout, QSizePolicy, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from parsers.models import Project
from reporting.builders.damwand_tekst import (
    RESULTATEN_GRAFIEK_INTRO_TEKST,
    RESULTATEN_INTRO_TEKST,
    RESULTATEN_TITEL,
)
from reporting.builders.result_description_builder import (
    _step_short_label,
    is_bgt_step_key,
    is_ugt_step_key,
)
from reporting.figure_renderer import render_figuur
from reporting.models import ReportImageGroup, ReportSection, ReportTable
from ui.table_styles import (
    TABLE_BORDER, TABLE_EXTRA_COLOR, TABLE_FONT, TABLE_HEADER_BG,
    TABLE_HEADER_FG, TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG,
    TABLE_LABEL_COLOR, TABLE_ROW_EVEN_BG, TABLE_ROW_ODD_BG, TABLE_ROW_SEP,
    TABLE_HEADER_SIZE, TABLE_TEXT_SIZE, TABLE_VALUE_COLOR,
)
from utils.formatting import fmt_number

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
_EXTRA_CLR  = TABLE_EXTRA_COLOR
_FONT       = TABLE_FONT
_HDR_PT     = TABLE_HEADER_SIZE
_DATA_PT    = TABLE_TEXT_SIZE
_PARAM_STRETCH = 5
_WAARDE_STRETCH = 3
_EENHEID_STRETCH = 2
_STAP_STRETCH = 2
_SPEC_TABLE_STRETCH = 10
_SPEC_TABLE_REST_STRETCH = 6
_SPEC_DATA_MIN_HEIGHT_PX = 27
_REPORT_TABLE_STRETCH = 10
_REPORT_TABLE_REST_STRETCH = 6
_FIGURE_TABLE_IMAGE_MIN_W = 240
_FIGURE_TABLE_IMAGE_MIN_H = 300
_FIGURE_RENDER_W = 300
_FIGURE_RENDER_H = 360


class TabResultDesc(QWidget):
    """Toont resultaattabel en gegenereerde resultaatbeschrijvingen (Tab 3B)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._tabel_widget: QWidget | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Scrollgebied
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(12)
        self._main_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    # Publieke API
    # ------------------------------------------------------------------

    def populate_resultaat_tabel(self, project: Project | None) -> None:
        """Sla het project op en render de resultaattabel."""
        self._project = project
        if not project or not project.result_summaries:
            self._clear_tabel()
            return
        self._render_tabel()

    def populate(self, sections: list[ReportSection]) -> None:
        """Voeg gegenereerde tekstsecties toe (bestaande API, ongewijzigd)."""
        # Verwijder alleen de dynamische tekstsecties, niet de specificatietabel.
        verwijder = []
        for i in range(self._main_layout.count()):
            widget = self._main_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox) or (
                widget is not None and widget.property('resultDescDynamic')
            ):
                verwijder.append(widget)
        for w in verwijder:
            w.deleteLater()

        if not sections:
            return

        for sec in sections:
            box = QGroupBox('')
            box.setStyleSheet(
                'QGroupBox { background: white; border: 1px solid #cfd6dd; '
                'border-radius: 8px; margin-top: 4px; padding: 4px; }'
            )
            box.setProperty('resultDescDynamic', True)
            vl = QVBoxLayout(box)
            vl.setContentsMargins(0, 4, 0, 0)
            vl.setSpacing(6)
            for field in sec.fields:
                val = f'{field.value} {field.unit}'.strip() if field.unit else field.value
                lbl = QLabel(f'<b>{field.label}:</b> {val}')
                lbl.setStyleSheet('padding: 0 8px;')
                vl.addWidget(lbl)
            gebruik_tabs = len(sec.tables) > 1 or (
                len(sec.tables) == 1 and bool(sec.tables[0].title)
            )
            if gebruik_tabs:
                tabs = QTabWidget()
                tabs.setDocumentMode(True)
                for table in sec.tables:
                    tabs.addTab(self._maak_styled_tabel(table), table.title)
                vl.addWidget(tabs)
            else:
                for table in sec.tables:
                    vl.addWidget(self._maak_styled_tabel(table))

            for groep in sec.image_groups:
                vl.addWidget(self._maak_figuurgroep_widget(groep))

            toelichting = self._maak_tabel_toelichting(sec.id) if sec.tables else None
            if sec.image_groups and toelichting is None:
                toelichting = self._maak_tabel_toelichting(sec.id)
            titel = None
            if sec.tables:
                titel = self._maak_sectie_titel_label(sec.title)
            if titel is not None:
                titel.setProperty('resultDescDynamic', True)
                self._main_layout.insertWidget(self._main_layout.count() - 1, titel)
            if toelichting is not None:
                toelichting.setProperty('resultDescDynamic', True)
                self._main_layout.insertWidget(self._main_layout.count() - 1, toelichting)
            if sec.fields or sec.tables or sec.text_blocks or sec.image_groups:
                self._main_layout.insertWidget(self._main_layout.count() - 1, box)
                if sec.id == 'extremen_overzicht':
                    conclusie = self._maak_resultaat_conclusie_label()
                    conclusie.setProperty('resultDescDynamic', True)
                    self._main_layout.insertWidget(
                        self._main_layout.count() - 1, conclusie
                    )

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _maak_sectie_titel_label(self, tekst: str) -> QLabel:
        lbl = QLabel(tekst)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 18px; font-weight: 700; '
            f'color: {_LABEL_CLR}; background: transparent; padding: 0px 4px 4px 4px;'
        )
        return lbl

    def _maak_toelichting_label(self, tekst: str) -> QLabel:
        """Maak een toelichting in dezelfde stijl als de grondsoortentabel."""
        lbl = QLabel(tekst)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f'font-family: {_FONT}; font-size: 12px; color: {_LABEL_CLR}; '
            f'background: transparent; padding: 0px 4px 12px 4px;'
        )
        return lbl

    def _maak_tabel_toelichting(self, section_id: str) -> QLabel | None:
        teksten = {
            'anchor_forces': (
                'In deze tabel zijn per fase de berekende anker- en stempelkrachten '
                'weergegeven voor de aanwezige CUR 166-toetsstappen. Ontbrekende '
                'waarden betekenen dat voor die fase en toetsstap geen resultaat is '
                'gerapporteerd.'
            ),
            'per_phase_summary': (
                'In deze tabel staan per fase de maximale absolute waarden voor '
                'momenten, dwarskrachten en vervormingen. De kolommen zijn gegroepeerd '
                'per resultaatsoort en uitgesplitst naar de beschikbare toetsstappen.'
            ),
            'extremen_overzicht': (
                RESULTATEN_GRAFIEK_INTRO_TEKST
            ),
        }
        tekst = teksten.get(section_id)
        return self._maak_toelichting_label(tekst) if tekst else None

    def _maak_resultaat_conclusie_label(self) -> QLabel:
        """Maak de conclusie onder de maatgevende-resultatenfiguren."""
        return self._maak_toelichting_label(self._resultaat_conclusie_tekst())

    def _resultaat_conclusie_tekst(self) -> str:
        """Geef een korte conclusie op basis van de maatgevende resultaten."""
        msd, _dsd, vervorming = self._maatgevende_waarden()
        moment_zin = (
            'de berekende momenten opneembaar zijn'
            if self._moment_is_opneembaar(msd)
            else 'de opneembaarheid van de berekende momenten nader beoordeeld moet worden'
        )
        verplaatsing = fmt_number(vervorming)
        return (
            'Op basis van bovenstaande resultaten kan worden geconcludeerd dat '
            f'{moment_zin}. De berekende topverplaatsing bij de doorsnede is '
            f'{verplaatsing}mm. Op basis hiervan wordt voldaan aan de '
            'verplaatsingseis.'
        )

    def _moment_is_opneembaar(self, msd: float | None) -> bool:
        """Geef True als Msd niet groter is dan het opneembare moment."""
        if not self._project or not self._project.sheet_piling or msd is None:
            return True
        opneembaar = self._project.sheet_piling[0].opneembaar_moment_knm
        return abs(msd) <= opneembaar

    def _maak_figuurgroep_widget(self, groep: ReportImageGroup) -> QWidget:
        """Rendert een ReportImageGroup als 3x3 figuurtabel in de UI."""
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        buitenste = QHBoxLayout(wrapper)
        buitenste.setContentsMargins(0, 0, 0, 0)
        buitenste.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame)

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n_cols = len(groep.headers)
        for col in range(n_cols):
            grid.setColumnStretch(col, 1)

        for col, header in enumerate(groep.headers):
            lbl = QLabel(header)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            lbl.setWordWrap(True)
            border_r = f'border-right: 1px solid {_BORDER};' if col < n_cols - 1 else ''
            lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_HDR_FG}; background: {_HDR_BG}; '
                f'padding: 3px 6px; min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_r}'
            )
            grid.addWidget(lbl, 0, col)

        for col, img_req in enumerate(groep.images):
            img_lbl = QLabel('-')
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            img_lbl.setMinimumSize(_FIGURE_TABLE_IMAGE_MIN_W, _FIGURE_TABLE_IMAGE_MIN_H)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < n_cols - 1 else ''
            img_lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_EXTRA_CLR}; '
                f'background: {_ROW_ODD_BG}; padding: 6px; '
                f'border-bottom: 1px solid {_ROW_SEP}; {border_r}'
            )
            if img_req is not None and self._project is not None:
                png = render_figuur(img_req, self._project)
                if png:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(png):
                        img_lbl.setText('')
                        img_lbl.setPixmap(
                            pixmap.scaled(
                                _FIGURE_RENDER_W, _FIGURE_RENDER_H,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
            grid.addWidget(img_lbl, 1, col)

        for col, footer in enumerate(groep.footers):
            lbl = QLabel(footer)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            lbl.setWordWrap(True)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < n_cols - 1 else ''
            lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_VALUE_CLR}; '
                f'background: {_ROW_EVN_BG}; padding: 2px 6px; '
                f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_r}'
            )
            grid.addWidget(lbl, 2, col)

        return wrapper

    def _maak_styled_tabel(self, table: ReportTable) -> QWidget:
        """Rendert een ReportTable als gestijlde grid-tabel.

        Ondersteunt optioneel een groepkop-rij (rij 0) wanneer
        table.column_groups gevuld is; kolomkoppen komen dan op rij 1.
        """
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        buitenste = QHBoxLayout(wrapper)
        buitenste.setContentsMargins(0, 0, 0, 0)
        buitenste.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame, stretch=_REPORT_TABLE_STRETCH)
        buitenste.addStretch(_REPORT_TABLE_REST_STRETCH)

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n_cols = len(table.columns)
        heeft_groepen = bool(table.column_groups)
        kop_rij = 1 if heeft_groepen else 0
        data_start = kop_rij + 1

        # Groepkoppen (grid-rij 0) — alleen als column_groups gevuld is
        if heeft_groepen:
            col_offset = 0
            for groep_label, colspan in table.column_groups:
                lbl = QLabel(groep_label)
                lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                groep_bg = _HDR_BG if not groep_label else _SUBHDR_BG
                border_r = (f'border-right: 1px solid {_BORDER};'
                             if col_offset + colspan < n_cols else '')
                lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                    f'color: {_HDR_FG}; background: {groep_bg}; '
                    f'padding: 3px 6px; min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_r}'
                )
                grid.addWidget(lbl, 0, col_offset, 1, colspan)
                col_offset += colspan

        # Kolomkoppen (grid-rij kop_rij)
        for col, kop in enumerate(table.columns):
            lbl = QLabel(kop)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if col < n_cols - 1 else ''
            lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_SUBHDR_FG}; background: {_HDR_BG}; '
                f'padding: 3px 6px; min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_r}'
            )
            grid.addWidget(lbl, kop_rij, col)

        # Datarijen (grid-rij data_start+)
        for row_i, rij in enumerate(table.rows):
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVN_BG
            is_last = row_i == len(table.rows) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            for col, cel in enumerate(rij):
                uitlijning = (Qt.AlignmentFlag.AlignLeft if col == 0
                              else Qt.AlignmentFlag.AlignRight)
                cel_lbl = QLabel(cel)
                cel_lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                cel_lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
                border_r = (f'border-right: 1px solid {_ROW_SEP};'
                             if col < n_cols - 1 else '')
                cel_lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 2px 6px; '
                    f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_r} {border_b}'
                )
                grid.addWidget(cel_lbl, data_start + row_i, col)

        return wrapper

    def _clear_tabel(self) -> None:
        """Verwijder de resultaattabel-widget als die bestaat."""
        if self._tabel_widget is not None:
            self._tabel_widget.deleteLater()
            self._tabel_widget = None

    def _render_tabel(self) -> None:
        self._clear_tabel()
        if not self._project:
            return
        self._tabel_widget = self._maak_tabel()
        self._main_layout.insertWidget(0, self._tabel_widget)

    def _maatgevende_waarden(self) -> tuple[float | None, float | None, float | None]:
        """Bereken Msd, Dsd en Vervorming projectbreed vanuit result_steps.

        Returns
        -------
        tuple[float | None, float | None, float | None]
            (msd, dsd, vervorming): maximale absolute waarden over alle fases.
            Msd/Dsd: maximum over UGT-stappen 6.1 t/m 6.4 plus 6.5 x factor.
            Vervorming: maximum over alle fases, uitsluitend uit BGT-stap 6.5.
        """
        msd, dsd, vervorming = self._maatgevende_waarden_met_stappen()
        return msd[0], dsd[0], vervorming[0]

    def _maatgevende_waarden_met_stappen(
        self,
    ) -> tuple[
        tuple[float | None, str | None],
        tuple[float | None, str | None],
        tuple[float | None, str | None],
    ]:
        """Bereken maatgevende waarden inclusief verificatiestap."""
        if not self._project or not self._project.result_steps:
            return (None, None), (None, None), (None, None)

        msd: float | None = None
        dsd: float | None = None
        msd_stap: str | None = None
        dsd_stap: str | None = None

        for stap_key, step in self._project.result_steps.items():
            if not is_ugt_step_key(stap_key):
                continue
            for rs in step.stages.values():
                for pt in rs.points:
                    v = abs(pt.moment)
                    if msd is None or v > msd:
                        msd = v
                        msd_stap = stap_key
                    v = abs(pt.shear)
                    if dsd is None or v > dsd:
                        dsd = v
                        dsd_stap = stap_key

        vervorming: float | None = None
        vervorming_stap: str | None = None
        for stap_key, step in self._project.result_steps.items():
            if not is_bgt_step_key(stap_key):
                continue
            for rs in step.stages.values():
                for pt in rs.points:
                    v = abs(pt.disp)
                    if vervorming is None or v > vervorming:
                        vervorming = v
                        vervorming_stap = stap_key

        return (msd, msd_stap), (dsd, dsd_stap), (vervorming, vervorming_stap)

    def _formatteer_stap(self, stap_key: str | None) -> str:
        """Formatteer een verificatiestap voor de app-tabel."""
        return f'stap {_step_short_label(stap_key)}' if stap_key else ''

    def _maak_tabel(self) -> QWidget:
        """Bouw de resultaattabel met projectbrede maatgevende waarden."""
        project = self._project
        el = project.sheet_piling[0] if project and project.sheet_piling else None
        summaries = project.result_summaries if project else []

        # Maatgevende samenvatting: hoogste mob_moment_pct over alle fases
        maatgevend = max(summaries, key=lambda s: s.mob_moment_pct, default=None)
        max_mob_mom = max((s.mob_moment_pct for s in summaries), default=0.0)
        max_mob_grond = max((s.mob_grond_pct for s in summaries), default=0.0)

        rijen: list[tuple[str, str, str, str]] = []

        # Damwandsectie
        rijen.append(('Grondkering', '', '', ''))
        rijen.append(('Profiel', el.name.split('(')[0].strip() if el else '-', '[-]', ''))
        rijen.append(('Staalkwaliteit', el.steel_quality if el else '-', '[-]', ''))
        rijen.append(('Opneembaar moment', fmt_number(el.opneembaar_moment_knm) if el else '-', '[kNm/m]', ''))
        rijen.append(('Niveau b.k.', fmt_number(el.top or 0.0) if el else '-', '[m NAP]', ''))
        rijen.append(('Niveau o.k.', fmt_number(el.bottom) if el else '-', '[m NAP]', ''))
        rijen.append(('Lengte', fmt_number(abs((el.top or 0.0) - el.bottom)) if el else '-', '[m]', ''))

        # Resultaten (projectbreed)
        msd, dsd, vervorming = self._maatgevende_waarden_met_stappen()
        rijen.append(('Resultaten', '', '', 'Verificatiestap'))
        rijen.append(('Moment Msd UGT', fmt_number(msd[0]), '[kNm/m]', self._formatteer_stap(msd[1])))
        rijen.append(('Dwarskracht Dsd UGT', fmt_number(dsd[0]), '[kN/m]', self._formatteer_stap(dsd[1])))
        rijen.append(('Verplaatsing urep BGT', fmt_number(vervorming[0]), '[mm]', self._formatteer_stap(vervorming[1])))
        rijen.append(('Gemobiliseerd Moment', fmt_number(max_mob_mom), '[%]', ''))
        rijen.append(('Gemobiliseerd Grond', fmt_number(max_mob_grond), '[%]', ''))

        if maatgevend:
            for naam, kracht, niveau in maatgevend.ondersteuningen[:4]:
                rijen.append((naam, fmt_number(kracht), '[kN/m]', ''))
                rijen.append((f'Niveau {naam}', fmt_number(niveau), '[m NAP]', ''))

        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        wrapper_lay = QVBoxLayout(wrapper)
        wrapper_lay.setContentsMargins(0, 0, 0, 0)
        wrapper_lay.setSpacing(0)

        wrapper_lay.addWidget(self._maak_sectie_titel_label(RESULTATEN_TITEL))
        wrapper_lay.addWidget(self._maak_toelichting_label(RESULTATEN_INTRO_TEKST))

        tabel_rij = QWidget()
        tabel_rij_layout = QHBoxLayout(tabel_rij)
        tabel_rij_layout.setContentsMargins(0, 0, 0, 0)
        tabel_rij_layout.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        grid_w = QWidget()
        grid_w.setStyleSheet('background: white; border: none;')
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        # Kolomvolgorde: label | verificatiestap | waarde | eenheid
        grid.setColumnStretch(0, _PARAM_STRETCH)
        grid.setColumnStretch(1, _STAP_STRETCH)
        grid.setColumnStretch(2, _WAARDE_STRETCH)
        grid.setColumnStretch(3, _EENHEID_STRETCH)

        data_index = 0
        for i, (label, waarde, eenheid, stap) in enumerate(rijen):
            is_sectie = waarde == '' and eenheid == ''
            is_last = i == len(rijen) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            bg = _HDR_BG if is_sectie else (
                _ROW_ODD_BG if data_index % 2 == 0 else _ROW_EVN_BG
            )

            lbl = QLabel(label)
            lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            hdr_stijl = (
                f'font-family: {_FONT}; font-size: {_HDR_PT}pt; font-weight: 700; '
                f'color: {_HDR_FG}; background: {bg}; padding: 3px 6px; '
                f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_b}'
            )

            if is_sectie:
                lbl.setStyleSheet(hdr_stijl)
                if stap:
                    # "Resultaten"-type: label col 0, stap-header cols 1-3
                    grid.addWidget(lbl, i, 0, 1, 1)
                    stap_lbl = QLabel(stap)
                    stap_lbl.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
                    stap_lbl.setAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    stap_lbl.setStyleSheet(hdr_stijl)
                    grid.addWidget(stap_lbl, i, 1, 1, 3)
                else:
                    # "Grondkering"-type: span alle 4 kolommen
                    grid.addWidget(lbl, i, 0, 1, 4)
                continue

            # Datarij
            lbl_stijl = (
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-weight: 400; '
                f'color: {_LABEL_CLR}; background: {bg}; padding: 2px 6px; '
                f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            val_stijl = (
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; color: {_VALUE_CLR}; '
                f'background: {bg}; padding: 2px 6px; '
                f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; '
                f'border-right: 1px solid {_ROW_SEP}; {border_b}'
            )
            ext_stijl = (
                f'font-family: {_FONT}; font-size: {_DATA_PT}pt; font-style: italic; '
                f'color: {_EXTRA_CLR}; background: {bg}; padding: 2px 6px; '
                f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; {border_b}'
            )

            val = QLabel(waarde)
            val.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            val.setStyleSheet(val_stijl)

            ext = QLabel(eenheid)
            ext.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
            ext.setStyleSheet(ext_stijl)

            if stap:
                # Rij mét verificatiestap: label | stap | waarde | eenheid
                lbl.setStyleSheet(lbl_stijl)
                grid.addWidget(lbl, i, 0)

                stap_cel = QLabel(stap)
                stap_cel.setMinimumHeight(_SPEC_DATA_MIN_HEIGHT_PX)
                stap_cel.setAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                stap_cel.setStyleSheet(
                    f'font-family: {_FONT}; font-size: {_DATA_PT}pt; '
                    f'color: {_EXTRA_CLR}; background: {bg}; padding: 2px 6px; '
                    f'min-height: {_SPEC_DATA_MIN_HEIGHT_PX}px; '
                    f'border-right: 1px solid {_ROW_SEP}; {border_b}'
                )
                grid.addWidget(stap_cel, i, 1)
                grid.addWidget(val, i, 2)
                grid.addWidget(ext, i, 3)
            else:
                # Rij zonder stap: label (cols 0+1 samengevoegd) | waarde | eenheid
                lbl.setStyleSheet(lbl_stijl)
                grid.addWidget(lbl, i, 0, 1, 2)
                grid.addWidget(val, i, 2)
                grid.addWidget(ext, i, 3)

            data_index += 1

        lay.addWidget(grid_w)
        tabel_rij_layout.addWidget(frame, stretch=_SPEC_TABLE_STRETCH)
        tabel_rij_layout.addStretch(_SPEC_TABLE_REST_STRETCH)
        wrapper_lay.addWidget(tabel_rij)
        return wrapper
