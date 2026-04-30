"""WordHoofdstukExporter — exporteert het damwand-hoofdstuk naar Word."""
from __future__ import annotations
from pathlib import Path

from docx import Document
from docx.shared import Cm

from reporting.models import ReportSection, ReportMetadata
from reporting.figure_renderer import render_figuur


class WordHoofdstukExporter:
    """Schrijft een lijst van ReportSection objecten naar een .docx bestand."""

    def export(
        self,
        sections: list[ReportSection],
        metadata: ReportMetadata,
        project,
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

    def _schrijf_sectie(self, doc: Document, sec: ReportSection, project) -> None:
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
            import io
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
