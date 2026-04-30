"""HtmlPreviewBuilder — genereert een HTML-string uit een ReportPackage."""

from __future__ import annotations

import base64

from reporting.models import ReportPackage, ReportSection, ReportField, ReportTable
from reporting.figure_renderer import render_figuur

# ── Kleurconstanten (consistent met app-stijl) ───────────────────────────────
_HDR_BG   = '#147ACF'
_HDR_FG   = '#ffffff'
_SUB_BG   = '#147ACF'
_SUB_FG   = '#ffffff'
_ODD_BG   = '#ffffff'
_EVEN_BG  = '#f2f2f2'
_SEP      = '#000000'
_LABEL    = '#000000'
_VALUE    = '#000000'
_FONT     = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'

_CSS = f"""
  body {{ font-family: {_FONT}; font-size: 12px; color: {_VALUE};
          margin: 0; padding: 16px; background: #ffffff; }}
  h1   {{ font-size: 15px; font-weight: 700; color: {_HDR_BG};
          border-bottom: 2px solid {_HDR_BG}; padding-bottom: 6px;
          margin-bottom: 16px; }}
  h2   {{ font-size: 12px; font-weight: 700; color: {_SUB_BG};
          margin: 18px 0 6px 0; padding: 5px 10px;
          background: #eaf2f8; border-left: 3px solid {_SUB_BG}; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px;
           border: 1px solid {_SEP}; }}
  th    {{ background: {_HDR_BG}; color: {_HDR_FG}; font-size: 11px;
           font-weight: 600; padding: 5px 10px; text-align: left;
           border: 1px solid {_SEP}; }}
  td    {{ padding: 5px 10px; border: 1px solid {_SEP};
           font-size: 11px; }}
  tr.odd  td {{ background: {_ODD_BG}; }}
  tr.even td {{ background: {_EVEN_BG}; }}
  td.label {{ color: {_LABEL}; font-weight: 500; width: 45%; }}
  td.value {{ text-align: right; }}
  td.unit  {{ color: {_VALUE}; font-size: 10px; width: 20%; }}
  p.tekst  {{ font-size: 11px; color: #3d4f5c; margin: 4px 0 10px 0;
              line-height: 1.6; }}
  p.caption {{ font-size: 10px; color: #666666; margin: 2px 0 10px 0; }}
  p.leeg   {{ color: #a0b4c2; font-style: italic; padding: 20px 0; }}
  img.figuur {{ max-width: 100%; margin: 8px 0 2px 0; }}
  img.figuur-cel {{ width: 100%; max-width: 100%; margin: 4px 0; }}
  table.figuurgroep td {{ vertical-align: top; text-align: center; }}
  table.figuurgroep .bron {{ font-size: 10px; color: #555555; }}
  .inline-wrap td {{ vertical-align: top; padding-right: 16px; }}
  .inline-wrap {{ border-collapse: separate; border-spacing: 0; width: auto;
                  margin-bottom: 12px; border: none; }}
  .inline-wrap table {{ width: auto; min-width: 160px; margin-bottom: 0; }}
"""


class HtmlPreviewBuilder:
    """Zet een ReportPackage om naar een HTML-string voor QTextBrowser."""

    def build(self, package: ReportPackage, project=None) -> str:
        """Genereer HTML-string voor de geselecteerde secties.

        Parameters
        ----------
        package:
            Rapportpakket met invoer-, resultaat- en extra-secties en de selectielijst.
        project:
            Actief project voor het renderen van figuren; ``None`` laat figuren weg.

        Returns
        -------
        str
            Volledige HTML-string geschikt voor QTextBrowser.setHtml().
        """
        titel = package.metadata.project_name or 'Rapport'

        alle_secties: dict[str, ReportSection] = {
            s.id: s
            for s in (
                package.input_sections
                + package.result_sections
                + package.extra_sections
            )
        }

        secties: list[str] = []
        for item in package.selected_items:
            if not item.included_word:
                continue
            sec = alle_secties.get(item.source_ref)
            if sec is not None:
                secties.append(self._sectie_html(sec, project))

        body = (
            '\n'.join(secties)
            if secties
            else '<p class="leeg">Geen secties geselecteerd.</p>'
        )

        return (
            f'<!DOCTYPE html><html><head>'
            f'<meta charset="utf-8">'
            f'<style>{_CSS}</style>'
            f'</head><body>'
            f'<h1>{_esc(titel)}</h1>'
            f'{body}'
            f'</body></html>'
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sectie_html(self, sec: ReportSection, project=None) -> str:
        """Render één ReportSection als HTML-fragment."""
        delen: list[str] = [f'<h2>{_esc(sec.title)}</h2>']

        if sec.fields:
            delen.append(self._velden_html(sec.fields))

        # Inline tabellen naast elkaar in flex-container; overige tabellen gestapeld
        inline = [t for t in sec.tables if t.inline]
        normaal = [t for t in sec.tables if not t.inline]
        if inline:
            cellen = ''.join(
                f'<td>{self._tabel_html(t)}</td>' for t in inline
            )
            delen.append(
                f'<table class="inline-wrap"><tr>{cellen}</tr></table>'
            )
        for tabel in normaal:
            delen.append(self._tabel_html(tabel))

        for blok in sec.text_blocks:
            tekst = blok.effective_text
            if tekst:
                delen.append(f'<p class="tekst">{_esc(tekst)}</p>')

        for groep in sec.image_groups:
            groep_html = self._figuurgroep_html(groep, project)
            if groep_html:
                delen.append(groep_html)

        for img_req in sec.images:
            figuur_html = self._figuur_html(img_req, project)
            if figuur_html:
                delen.append(figuur_html)

        return '\n'.join(delen)

    def _figuur_html(self, img_req, project=None) -> str:
        """Render een figuur als base64 data-URI voor de HTML-preview."""
        if project is None:
            return ''
        png = render_figuur(img_req, project)
        if not png:
            return ''
        b64 = base64.b64encode(png).decode('ascii')
        caption = (
            f'<p class="caption">{_esc(img_req.caption)}</p>'
            if img_req.caption else ''
        )
        return f'<img class="figuur" src="data:image/png;base64,{b64}">{caption}'

    def _figuurgroep_html(self, groep, project=None) -> str:
        """Render een groep figuren als 3-rijen tabel."""
        if not groep.headers:
            return ''

        header = ''.join(f'<th>{_esc(kop)}</th>' for kop in groep.headers)
        figuur_cellen: list[str] = []
        for img_req in groep.images:
            if img_req is None or project is None:
                figuur_cellen.append('<td>-</td>')
                continue
            png = render_figuur(img_req, project)
            if not png:
                figuur_cellen.append('<td>-</td>')
                continue
            b64 = base64.b64encode(png).decode('ascii')
            figuur_cellen.append(
                f'<td><img class="figuur-cel" '
                f'src="data:image/png;base64,{b64}"></td>'
            )
        footer = ''.join(
            f'<td class="bron">{_esc(tekst)}</td>' for tekst in groep.footers
        )
        titel = (
            f'<p style="font-size:11px;font-weight:600;color:{_LABEL};'
            f'margin:8px 0 3px;">{_esc(groep.title)}</p>'
            if groep.title else ''
        )
        return (
            f'{titel}<table class="figuurgroep">'
            f'<tr>{header}</tr>'
            f'<tr>{"".join(figuur_cellen)}</tr>'
            f'<tr>{footer}</tr>'
            f'</table>'
        )

    def _velden_html(self, velden: list[ReportField]) -> str:
        """Render veld-rijen als HTML-tabel."""
        rijen = []
        for i, veld in enumerate(velden):
            klasse = 'odd' if i % 2 == 0 else 'even'
            unit_cel = f'<td class="unit">{_esc(veld.unit)}</td>' if veld.unit else '<td></td>'
            rijen.append(
                f'<tr class="{klasse}">'
                f'<td class="label">{_esc(veld.label)}</td>'
                f'<td class="value">{_esc(veld.value)}</td>'
                f'{unit_cel}'
                f'</tr>'
            )
        return f'<table>{"".join(rijen)}</table>'

    def _tabel_html(self, tabel: ReportTable) -> str:
        """Render een ReportTable als HTML-tabel met header."""
        seps = set(tabel.separator_before_cols)
        sep_style = f'border-left: 2px solid {_SEP};'

        def th(i: int, k: str) -> str:
            st = f' style="{sep_style}"' if i in seps else ''
            return f'<th{st}>{_esc(k)}</th>'

        def td(i: int, cel: str) -> str:
            st = f' style="{sep_style}"' if i in seps else ''
            return f'<td{st}>{_esc(cel)}</td>'

        if tabel.column_groups:
            # Eerste headerrij: groepkoppen met colspan (geen rowspan)
            col_idx = 0
            groep_cellen: list[str] = []
            for label, span in tabel.column_groups:
                st = ''
                if col_idx in seps:
                    st = f' style="text-align:center;{sep_style}"'
                elif label:
                    st = ' style="text-align:center;"'
                groep_cellen.append(
                    f'<th{st} colspan="{span}">{_esc(label)}</th>'
                )
                col_idx += span
            groep_rij = f'<tr>{"".join(groep_cellen)}</tr>'
            # Tweede headerrij: alle individuele kolomkoppen
            header = ''.join(th(i, k) for i, k in enumerate(tabel.columns))
            header_html = f'{groep_rij}<tr>{header}</tr>'
        else:
            header = ''.join(th(i, k) for i, k in enumerate(tabel.columns))
            header_html = f'<tr>{header}</tr>'

        rijen = []
        for row_i, rij in enumerate(tabel.rows):
            klasse = 'odd' if row_i % 2 == 0 else 'even'
            cellen = ''.join(td(i, cel) for i, cel in enumerate(rij))
            rijen.append(f'<tr class="{klasse}">{cellen}</tr>')
        if tabel.title:
            kop = f'<p style="font-size:11px;font-weight:600;color:{_LABEL};margin:8px 0 3px;">{_esc(tabel.title)}</p>'
        else:
            kop = ''
        return f'{kop}<table>{header_html}{"".join(rijen)}</table>'


def _esc(tekst: object) -> str:
    """Vervang HTML-speciale tekens door entiteiten.

    Parameters
    ----------
    tekst:
        Te escapen waarde; wordt eerst naar str geconverteerd.

    Returns
    -------
    str
        HTML-veilige string met speciale tekens vervangen door entiteiten.
    """
    return (
        str(tekst)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )
