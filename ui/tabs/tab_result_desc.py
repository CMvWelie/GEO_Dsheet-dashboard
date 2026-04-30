"""Tab 3B — Resultaatbeschrijving: gegenereerde tekst + maatgevende resultaattabel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QGroupBox, QGridLayout, QSizePolicy, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from parsers.models import Project
from reporting.builders.result_description_builder import (
    is_bgt_step_key,
    is_ugt_step_key,
)
from reporting.figure_renderer import render_figuur
from reporting.models import ReportImageGroup, ReportSection, ReportTable
from ui.table_styles import (
    TABLE_BORDER, TABLE_EXTRA_COLOR, TABLE_FONT, TABLE_HEADER_BG,
    TABLE_HEADER_FG, TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG,
    TABLE_LABEL_COLOR, TABLE_ROW_EVEN_BG, TABLE_ROW_ODD_BG, TABLE_ROW_SEP,
    TABLE_VALUE_COLOR,
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
            if len(sec.tables) > 1:
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
            titel = (
                self._maak_sectie_titel_label(sec.title)
                if sec.tables or sec.image_groups else None
            )
            if titel is not None:
                titel.setProperty('resultDescDynamic', True)
                self._main_layout.insertWidget(self._main_layout.count() - 1, titel)
            if toelichting is not None:
                toelichting.setProperty('resultDescDynamic', True)
                self._main_layout.insertWidget(self._main_layout.count() - 1, toelichting)
            if sec.fields or sec.tables or sec.text_blocks or sec.image_groups:
                self._main_layout.insertWidget(self._main_layout.count() - 1, box)

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
                'Deze figuurtabel toont de maatgevende UGT-waarden voor Msd en Dsd '
                '(CUR 166 6.1 t/m 6.4 plus 6.5 x factor) en de maatgevende BGT-'
                'verplaatsing Urep uit CUR 166 6.5.'
            ),
        }
        tekst = teksten.get(section_id)
        return self._maak_toelichting_label(tekst) if tekst else None

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
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; font-weight: 700; '
                f'color: {_HDR_FG}; background: {_HDR_BG}; '
                f'padding: 7px 10px; {border_r}'
            )
            grid.addWidget(lbl, 0, col)

        for col, img_req in enumerate(groep.images):
            img_lbl = QLabel('-')
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            img_lbl.setMinimumSize(240, 300)
            border_r = f'border-right: 1px solid {_ROW_SEP};' if col < n_cols - 1 else ''
            img_lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 12px; color: {_EXTRA_CLR}; '
                f'background: white; padding: 8px; '
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
                                300, 360,
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
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 11px; color: {_VALUE_CLR}; '
                f'background: {_ROW_ODD_BG}; padding: 7px 10px; {border_r}'
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
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame)
        buitenste.addStretch()

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
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 10px; font-weight: 700; '
                    f'color: {_HDR_FG}; background: {groep_bg}; '
                    f'padding: 5px 10px; {border_r}'
                )
                grid.addWidget(lbl, 0, col_offset, 1, colspan)
                col_offset += colspan

        # Kolomkoppen (grid-rij kop_rij)
        for col, kop in enumerate(table.columns):
            lbl = QLabel(kop)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = f'border-right: 1px solid {_BORDER};' if col < n_cols - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: {_SUBHDR_FG}; background: {_HDR_BG}; '
                f'padding: 6px 10px; {border_r}'
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
                border_r = (f'border-right: 1px solid {_ROW_SEP};'
                             if col < n_cols - 1 else '')
                cel_lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 10px; {border_r} {border_b}'
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
        if not self._project or not self._project.result_steps:
            return None, None, None

        msd: float | None = None
        dsd: float | None = None

        for stap_key, step in self._project.result_steps.items():
            if not is_ugt_step_key(stap_key):
                continue
            for rs in step.stages.values():
                for pt in rs.points:
                    v = abs(pt.moment)
                    if msd is None or v > msd:
                        msd = v
                    v = abs(pt.shear)
                    if dsd is None or v > dsd:
                        dsd = v

        vervorming: float | None = None
        for stap_key, step in self._project.result_steps.items():
            if not is_bgt_step_key(stap_key):
                continue
            for rs in step.stages.values():
                for pt in rs.points:
                    v = abs(pt.disp)
                    if vervorming is None or v > vervorming:
                        vervorming = v

        return msd, dsd, vervorming

    def _maak_tabel(self) -> QWidget:
        """Bouw de resultaattabel met projectbrede maatgevende waarden."""
        project = self._project
        el = project.sheet_piling[0] if project and project.sheet_piling else None
        summaries = project.result_summaries if project else []

        # Maatgevende samenvatting: hoogste mob_moment_pct over alle fases
        maatgevend = max(summaries, key=lambda s: s.mob_moment_pct, default=None)
        max_mob_mom = max((s.mob_moment_pct for s in summaries), default=0.0)
        max_mob_grond = max((s.mob_grond_pct for s in summaries), default=0.0)

        rijen: list[tuple[str, str, str]] = []

        # Damwandsectie
        rijen.append(('Damwand', '', ''))
        rijen.append(('Profiel', el.name.split('(')[0].strip() if el else '-', '[-]'))
        rijen.append(('Staalkwaliteit', el.steel_quality if el else '-', '[-]'))
        rijen.append(('Opneembaar moment', fmt_number(el.opneembaar_moment_knm) if el else '-', '[kNm/m]'))
        rijen.append(('Niveau damwand b.k.', fmt_number(el.top or 0.0) if el else '-', '[m NAP]'))
        rijen.append(('Niveau damwand o.k.', fmt_number(el.bottom) if el else '-', '[m NAP]'))
        rijen.append(('Damwandlengte', fmt_number(abs((el.top or 0.0) - el.bottom)) if el else '-', '[m]'))

        # Resultaten (projectbreed)
        msd, dsd, vervorming = self._maatgevende_waarden()
        rijen.append(('Resultaten', '', ''))
        rijen.append(('Moment Msd', fmt_number(msd), '[kNm/m]'))
        rijen.append(('Dwarskracht Dsd', fmt_number(dsd), '[kN/m]'))
        rijen.append(('Gemobiliseerd Moment', fmt_number(max_mob_mom), '[%]'))
        rijen.append(('Gemobiliseerd Grond', fmt_number(max_mob_grond), '[%]'))
        rijen.append(('Verplaatsing urep BGT', fmt_number(vervorming), '[mm]'))

        if maatgevend:
            for naam, kracht, niveau in maatgevend.ondersteuningen[:4]:
                rijen.append((naam, fmt_number(kracht), '[kN/m]'))
                rijen.append((f'Niveau {naam}', fmt_number(niveau), '[m NAP]'))

        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        wrapper_lay = QVBoxLayout(wrapper)
        wrapper_lay.setContentsMargins(0, 0, 0, 0)
        wrapper_lay.setSpacing(0)

        wrapper_lay.addWidget(self._maak_sectie_titel_label('Specificaties'))
        wrapper_lay.addWidget(self._maak_toelichting_label(
            'In deze tabel zijn de belangrijkste damwandgegevens en maatgevende '
            'projectresultaten samengevat. De resultaatwaarden betreffen de maxima '
            'over de beschikbare fases en toetsstappen.'
        ))

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.setColumnMinimumWidth(0, 220)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(2, 100)

        for i, (label, waarde, eenheid) in enumerate(rijen):
            is_sectie = waarde == '' and eenheid == ''
            bg = _HDR_BG if is_sectie else (_ROW_ODD_BG if i % 2 == 0 else _ROW_EVN_BG)
            is_last = i == len(rijen) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            fg = _HDR_FG if is_sectie else _LABEL_CLR

            lbl = QLabel(label)
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: {"12px" if not is_sectie else "11px"}; '
                f'font-weight: {"700" if is_sectie else "500"}; color: {fg}; '
                f'background: {bg}; padding: 6px 12px; '
                f'border-right: 1px solid {_ROW_SEP if not is_sectie else _HDR_BG}; {border_b}'
            )
            grid.addWidget(lbl, i, 0)

            if not is_sectie:
                val = QLabel(waarde)
                val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                val.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 14px; '
                    f'border-right: 1px solid {_ROW_SEP}; {border_b}'
                )
                grid.addWidget(val, i, 1)

                ext = QLabel(eenheid)
                ext.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 11px; font-style: italic; '
                    f'color: {_EXTRA_CLR}; background: {bg}; padding: 6px 10px; {border_b}'
                )
                grid.addWidget(ext, i, 2)

        lay.addWidget(grid_w)
        wrapper_lay.addWidget(frame)
        return wrapper
