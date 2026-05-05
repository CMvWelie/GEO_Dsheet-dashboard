"""WordHoofdstukExporter — exporteert het damwand-hoofdstuk naar Word."""
from __future__ import annotations
import io
from pathlib import Path
import re
import struct

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.table import Table

from reporting.models import (
    FaseInvoerSectie,
    ReportImageRequest,
    ReportMetadata,
    ReportSection,
)
from reporting.figure_renderer import render_figuur


_FASE_RIJHOOGTE_CM = 0.45


def _png_hoogte_cm(png_bytes: bytes, breedte_cm: float) -> float:
    """Bereken de weergavehoogte in cm van een PNG bij vaste breedte.

    Parameters
    ----------
    png_bytes:
        PNG-bestand als bytes.
    breedte_cm:
        Gewenste weergavebreedte in cm.

    Returns
    -------
    float
        De bijbehorende hoogte in cm, of 0,0 bij ongeldige invoer.
    """
    if len(png_bytes) < 24:
        return 0.0
    w_px = struct.unpack('>I', png_bytes[16:20])[0]
    h_px = struct.unpack('>I', png_bytes[20:24])[0]
    if w_px == 0:
        return 0.0
    return breedte_cm * h_px / w_px


def _hex_zonder_hash(kleur: str) -> str:
    """Normaliseer een CSS-hexkleur naar Word-hex zonder ``#``."""
    kleur = (kleur or '').strip()
    if kleur.startswith('#'):
        kleur = kleur[1:]
    return kleur.upper() if re.fullmatch(r'[0-9A-Fa-f]{6}', kleur) else '000000'


def _eerste_fontfamilie(font_stack: str) -> str:
    """Haal de eerste fontnaam uit een CSS-font-stack."""
    eerste = (font_stack or 'Arial').split(',')[0].strip()
    return eerste.strip('"\'') or 'Arial'


class WordHoofdstukExporter:
    """Schrijft een lijst van ReportSection objecten naar een .docx bestand."""

    def export(
        self,
        sections: list[ReportSection],
        metadata: ReportMetadata,
        project: object | None,
        template_path: str | None,
        output_path: str,
    ) -> str | None:
        """Exporteer naar Word.

        Parameters
        ----------
        sections:      Gesorteerde lijst van ReportSection objecten.
        metadata:      Rapportagegegevens (projectnaam, auteur, etc.).
        project:       Project-object voor figuurrendering (mag None zijn als geen figuren).
        template_path: Pad naar het .docx stijlenbestand, of None voor leeg document.
        output_path:   Uitvoerpad voor het .docx bestand.

        Returns
        -------
        str | None
            None bij succes, foutmelding bij uitzondering.
        """
        try:
            doc = self._open_doc(template_path)
            self._pas_document_typografie_toe(doc)
            self._schrijf_titel(doc, metadata)
            for sec in sections:
                self._schrijf_sectie(doc, sec, project)
            doc.save(output_path)
            return None
        except Exception as exc:
            return str(exc)

    # ------------------------------------------------------------------
    # Document openen
    # ------------------------------------------------------------------

    def _open_doc(self, template_path: str | None) -> Document:
        if template_path and Path(template_path).exists():
            return Document(template_path)
        return Document()

    # ------------------------------------------------------------------
    # Titel
    # ------------------------------------------------------------------

    def _schrijf_titel(self, doc: Document, metadata: ReportMetadata) -> None:
        titel = metadata.project_name or 'Damwand rapport'
        doc.add_heading(titel, level=1)

    def _pas_document_typografie_toe(self, doc: Document) -> None:
        """Pas thematekstgrootte toe op standaardtekst buiten tabellen."""
        from ui import table_styles

        stijl = doc.styles['Normal']
        stijl.font.name = _eerste_fontfamilie(table_styles.TABLE_FONT)
        stijl.font.size = Pt(table_styles.BODY_TEXT_SIZE)

    # ------------------------------------------------------------------
    # Secties
    # ------------------------------------------------------------------

    def _schrijf_sectie(
        self,
        doc: Document,
        sec: ReportSection,
        project: object | None,
    ) -> None:
        if isinstance(sec, FaseInvoerSectie):
            self._schrijf_fase_sectie(doc, sec, project)
            return

        doc.add_heading(sec.title, level=2)
        for veld in sec.fields:
            waarde = f'{veld.value} {veld.unit}'.strip() if veld.unit else veld.value
            doc.add_paragraph(f'{veld.label}: {waarde}')
        for tabel in sec.tables:
            self._schrijf_tabel(doc, tabel)
        for tb in sec.text_blocks:
            doc.add_paragraph(tb.effective_text)
        for img_req in sec.images:
            self._schrijf_figuur(doc, img_req, project)

    def _schrijf_fase_sectie(
        self,
        doc: Document,
        sec: FaseInvoerSectie,
        project: object | None,
    ) -> None:
        """Schrijf een fase-sectie als tabel met invoer en doorsnede.

        Parameters
        ----------
        doc:
            Doeldocument.
        sec:
            Fase-sectie met ``fase_card``.
        project:
            Project voor het renderen van de doorsnede; mag ``None`` zijn.
        """
        kaart = sec.fase_card
        if kaart is None:
            doc.add_heading(sec.title, level=2)
            return

        doc.add_heading(sec.title, level=2)
        png_bytes: bytes | None = None
        if project is not None:
            img_req = ReportImageRequest(
                id=f'fase_{kaart.fase_num}_doorsnede',
                caption='',
                figure_key='section',
                stage_index=kaart.fase_num - 1,
                step_key=None,
            )
            png_bytes = render_figuur(img_req, project)

        n_data = sum(1 + len(rij.extra_lines) for rij in kaart.rows)
        teksthoogte_cm = max(n_data, 1) * _FASE_RIJHOOGTE_CM
        afbeeldingshoogte_cm = _png_hoogte_cm(png_bytes, 6.0) if png_bytes else 0.0
        n_padding = 1 if afbeeldingshoogte_cm > teksthoogte_cm else 0
        n_header = 2
        n_rows = n_header + max(n_data, 1) + n_padding

        tbl = doc.add_table(rows=n_rows, cols=4)
        tbl.autofit = False
        try:
            tbl.style = 'Table Grid'
        except KeyError:
            pass

        kolom_breedtes = [1701, 1134, 2835, 3572]
        self._stel_tabel_grid_in(tbl, [3.0, 2.0, 5.0, 6.3])
        for row in tbl.rows:
            for col_idx, cell in enumerate(row.cells[:4]):
                self._stel_cel_breedte(cell, kolom_breedtes[col_idx])

        cel_naam = tbl.rows[0].cells[0].merge(tbl.rows[0].cells[2])
        self._stel_cel_breedte(cel_naam, sum(kolom_breedtes[:3]))
        cel_naam.text = kaart.stage_name
        tbl.rows[0].cells[3].text = 'Afbeelding'

        tbl.rows[1].cells[0].text = 'Parameter'
        tbl.rows[1].cells[1].text = 'Niveau'
        tbl.rows[1].cells[2].text = 'Toelichting'
        tbl.rows[1].cells[3].text = ''

        grid_row = n_header
        for rij in kaart.rows:
            n_sub = 1 + len(rij.extra_lines)
            if n_sub > 1:
                label_cel = tbl.rows[grid_row].cells[0].merge(
                    tbl.rows[grid_row + n_sub - 1].cells[0]
                )
                niveau_cel = tbl.rows[grid_row].cells[1].merge(
                    tbl.rows[grid_row + n_sub - 1].cells[1]
                )
                self._stel_cel_breedte(label_cel, kolom_breedtes[0])
                self._stel_cel_breedte(niveau_cel, kolom_breedtes[1])
                self._stel_rijhoogte_twips(tbl.rows[grid_row], 54)
                for k in range(1, n_sub):
                    self._stel_rijhoogte_twips(tbl.rows[grid_row + k], 52)

            tbl.rows[grid_row].cells[0].text = rij.label
            tbl.rows[grid_row].cells[1].text = rij.value
            tbl.rows[grid_row].cells[2].text = rij.extra
            for k, extra_tekst in enumerate(rij.extra_lines):
                tbl.rows[grid_row + k + 1].cells[2].text = extra_tekst
            grid_row += n_sub

        if n_padding:
            pad_start = n_header + max(n_data, 1)
            pad_cel = tbl.rows[pad_start].cells[0].merge(tbl.rows[n_rows - 1].cells[2])
            self._stel_cel_breedte(pad_cel, sum(kolom_breedtes[:3]))
            self._stel_rijhoogte_twips(tbl.rows[pad_start], 52)

        self._pas_fase_tabel_opmaak_toe(tbl)

        img_cel = tbl.rows[n_header].cells[3]
        for rij_idx in range(n_header + 1, n_rows):
            img_cel = img_cel.merge(tbl.rows[rij_idx].cells[3])
        self._stel_cel_breedte(img_cel, kolom_breedtes[3])

        para = img_cel.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if png_bytes:
            run = para.add_run()
            run.add_picture(io.BytesIO(png_bytes), width=Cm(6))

        tc_pr = img_cel._tc.get_or_add_tcPr()
        v_align = OxmlElement('w:vAlign')
        v_align.set(qn('w:val'), 'center')
        tc_pr.append(v_align)

    def _pas_fase_tabel_opmaak_toe(self, tbl: Table) -> None:
        """Pas thema-font en headerkleuren toe op de fase-invoertabel."""
        from ui import table_styles

        font = _eerste_fontfamilie(table_styles.TABLE_FONT)
        for row in tbl.rows:
            for cell in row.cells:
                self._pas_cel_font_toe(
                    cell, font, '000000', bold=False,
                    size_pt=table_styles.TABLE_TEXT_SIZE,
                )

        header_bg = _hex_zonder_hash(table_styles.TABLE_HEADER_BG)
        header_fg = _hex_zonder_hash(table_styles.TABLE_HEADER_FG)
        subheader_bg = _hex_zonder_hash(table_styles.TABLE_HEADER_SUB_BG)
        subheader_fg = _hex_zonder_hash(table_styles.TABLE_HEADER_SUB_FG)
        for cell in tbl.rows[0].cells:
            self._stel_cel_vulling(cell, header_bg)
            self._pas_cel_font_toe(
                cell, font, header_fg, bold=True,
                size_pt=table_styles.TABLE_HEADER_SIZE,
            )
        for cell in tbl.rows[1].cells:
            self._stel_cel_vulling(cell, subheader_bg)
            self._pas_cel_font_toe(
                cell, font, subheader_fg, bold=True,
                size_pt=table_styles.TABLE_HEADER_SIZE,
            )

    def _pas_cel_font_toe(
        self,
        cell,
        font_name: str,
        color_hex: str,
        *,
        bold: bool,
        size_pt: int,
    ) -> None:
        """Zet font, kleur en gewicht voor alle runs in een Word-cel."""
        kleur = RGBColor.from_string(color_hex)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = font_name
                run.font.size = Pt(size_pt)
                run.font.bold = bold
                run.font.color.rgb = kleur
                r_pr = run._r.get_or_add_rPr()
                r_fonts = r_pr.rFonts
                if r_fonts is None:
                    r_fonts = OxmlElement('w:rFonts')
                    r_pr.append(r_fonts)
                r_fonts.set(qn('w:ascii'), font_name)
                r_fonts.set(qn('w:hAnsi'), font_name)

    def _stel_cel_vulling(self, cell, fill_hex: str) -> None:
        """Zet celvulling op een hexkleur zonder randstijlen te wijzigen."""
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = tc_pr.find(qn('w:shd'))
        if shd is None:
            shd = OxmlElement('w:shd')
            tc_pr.append(shd)
        shd.set(qn('w:fill'), fill_hex)

    def _stel_cel_breedte(self, cell, breedte_dxa: int) -> None:
        """Zet celbreedte in twips/dxa zoals Word die in ``tcW`` verwacht."""
        tc_pr = cell._tc.get_or_add_tcPr()
        tc_w = tc_pr.find(qn('w:tcW'))
        if tc_w is None:
            tc_w = OxmlElement('w:tcW')
            tc_pr.append(tc_w)
        tc_w.set(qn('w:w'), str(breedte_dxa))
        tc_w.set(qn('w:type'), 'dxa')

    def _stel_rijhoogte_twips(self, row, hoogte_twips: int) -> None:
        """Zet een compacte rijhoogte in Word-twips zonder exact-height regel."""
        tr_pr = row._tr.get_or_add_trPr()
        tr_height = tr_pr.find(qn('w:trHeight'))
        if tr_height is None:
            tr_height = OxmlElement('w:trHeight')
            tr_pr.append(tr_height)
        tr_height.set(qn('w:val'), str(hoogte_twips))

    def _stel_tabel_grid_in(self, tbl: Table, breedtes_cm: list[float]) -> None:
        """Stel vaste Word-kolombreedtes in via ``tblGrid``."""
        tbl_grid = tbl._tbl.find(qn('w:tblGrid'))
        if tbl_grid is None:
            tbl_grid = OxmlElement('w:tblGrid')
            tbl._tbl.insert(0, tbl_grid)
        else:
            for col in list(tbl_grid):
                tbl_grid.remove(col)

        for breedte_cm in breedtes_cm:
            grid_col = OxmlElement('w:gridCol')
            grid_col.set(qn('w:w'), str(round(breedte_cm * 567)))
            tbl_grid.append(grid_col)

    def _schrijf_tabel(self, doc: Document, tabel) -> None:
        if not tabel.columns:
            return
        if tabel.title:
            doc.add_paragraph(tabel.title)
        t = doc.add_table(rows=1, cols=len(tabel.columns))
        try:
            t.style = 'Table Grid'
        except KeyError:
            pass
        for col, header in enumerate(tabel.columns):
            t.rows[0].cells[col].text = header
        for data_rij in tabel.rows:
            rij = t.add_row()
            for col, cel in enumerate(data_rij):
                if col < len(rij.cells):
                    rij.cells[col].text = str(cel)

    # ------------------------------------------------------------------
    # Figuren (placeholder — wordt ingevuld in Task 6)
    # ------------------------------------------------------------------

    def _schrijf_figuur(self, doc: Document, img_req, project) -> None:
        """Render een figuur headless en voeg in als inline afbeelding."""
        if project is None:
            doc.add_paragraph(f'[Figuur: {img_req.caption}]')
            return
        png_bytes = self._render_figuur(img_req, project)
        if png_bytes:
            doc.add_paragraph(img_req.caption)
            doc.add_picture(io.BytesIO(png_bytes), width=Cm(16))
        else:
            doc.add_paragraph(f'[Figuur niet beschikbaar: {img_req.caption}]')

    def _render_figuur(self, img_req, project) -> bytes | None:
        """Render figuur naar PNG-bytes met headless matplotlib.

        Ondersteunde figure_key waarden:
        - 'section'      : dwarsdoorsnede via SectionRenderer
        - 'moment_shear' : moment + dwarskracht via OutputRenderer
        - 'displacement' : vervorming via OutputRenderer
        """
        return render_figuur(img_req, project)
