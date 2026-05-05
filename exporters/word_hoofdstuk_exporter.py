"""WordHoofdstukExporter — exporteert het damwand-hoofdstuk naar Word."""
from __future__ import annotations
import io
import math
from pathlib import Path
import struct

from docx import Document
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.table import Table

from reporting.models import (
    FaseInvoerSectie,
    ReportImageRequest,
    ReportMetadata,
    ReportSection,
)
from reporting.figure_renderer import render_figuur


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
        n_img = math.ceil(_png_hoogte_cm(png_bytes, 6.0) / 0.18) if png_bytes else 0
        n_total = max(n_data, n_img, 1)
        n_padding = n_total - n_data
        n_header = 2
        n_rows = n_header + n_total

        tbl = doc.add_table(rows=n_rows, cols=4)
        try:
            tbl.style = 'Table Grid'
        except KeyError:
            pass

        self._stel_tabel_grid_in(tbl, [3.0, 2.0, 5.0, 6.0])

        cel_naam = tbl.rows[0].cells[0].merge(tbl.rows[0].cells[2])
        cel_naam.text = kaart.stage_name
        tbl.rows[0].cells[3].text = 'Afbeelding'

        tbl.rows[1].cells[0].text = 'Parameter'
        tbl.rows[1].cells[1].text = 'Niveau'
        tbl.rows[1].cells[2].text = 'Toelichting'

        grid_row = n_header
        for rij in kaart.rows:
            n_sub = 1 + len(rij.extra_lines)
            if n_sub > 1:
                tbl.rows[grid_row].cells[0].merge(
                    tbl.rows[grid_row + n_sub - 1].cells[0]
                )
                tbl.rows[grid_row].cells[1].merge(
                    tbl.rows[grid_row + n_sub - 1].cells[1]
                )

            tbl.rows[grid_row].cells[0].text = rij.label
            tbl.rows[grid_row].cells[1].text = rij.value
            tbl.rows[grid_row].cells[2].text = rij.extra
            for k, extra_tekst in enumerate(rij.extra_lines):
                tbl.rows[grid_row + k + 1].cells[2].text = extra_tekst
            grid_row += n_sub

        if n_padding > 0:
            pad_start = n_header + n_data
            tbl.rows[pad_start].cells[0].merge(tbl.rows[n_rows - 1].cells[2])

        for rij_idx in range(n_header, n_rows):
            tbl.rows[rij_idx].height = Cm(0.18)
            tbl.rows[rij_idx].height_rule = WD_ROW_HEIGHT_RULE.EXACTLY

        img_cel = tbl.rows[0].cells[3]
        for rij_idx in range(1, n_rows):
            img_cel = img_cel.merge(tbl.rows[rij_idx].cells[3])

        para = img_cel.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if png_bytes:
            run = para.add_run()
            run.add_picture(io.BytesIO(png_bytes), width=Cm(6))

        tc_pr = img_cel._tc.get_or_add_tcPr()
        v_align = OxmlElement('w:vAlign')
        v_align.set(qn('w:val'), 'center')
        tc_pr.append(v_align)

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
