"""HtmlPreviewBuilder — genereert een HTML-string uit een ReportPackage."""

from __future__ import annotations

from reporting.models import ReportPackage, ReportSection, ReportField, ReportTable

# ── Kleurconstanten (consistent met app-stijl) ───────────────────────────────
_HDR_BG   = '#1b3a5c'
_HDR_FG   = '#ffffff'
_SUB_BG   = '#274f77'
_SUB_FG   = '#d0e8f5'
_ODD_BG   = '#f3f8fc'
_EVEN_BG  = '#ffffff'
_SEP      = '#dce8f0'
_LABEL    = '#2c3f52'
_VALUE    = '#0f1e2b'
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
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
  th    {{ background: {_HDR_BG}; color: {_HDR_FG}; font-size: 11px;
           font-weight: 600; padding: 5px 10px; text-align: left; }}
  td    {{ padding: 5px 10px; border-bottom: 1px solid {_SEP};
           font-size: 11px; }}
  tr.odd  td {{ background: {_ODD_BG}; }}
  tr.even td {{ background: {_EVEN_BG}; }}
  td.label {{ color: {_LABEL}; font-weight: 500; width: 45%; }}
  td.value {{ text-align: right; }}
  td.unit  {{ color: #5a7a8a; font-size: 10px; width: 20%; }}
  p.tekst  {{ font-size: 11px; color: #3d4f5c; margin: 4px 0 10px 0;
              line-height: 1.6; }}
  p.leeg   {{ color: #a0b4c2; font-style: italic; padding: 20px 0; }}
"""


class HtmlPreviewBuilder:
    """Zet een ReportPackage om naar een HTML-string voor QTextBrowser."""

    def build(self, package: ReportPackage) -> str:
        """Genereer HTML-string voor de geselecteerde secties.

        Parameters
        ----------
        package:
            Rapportpakket met invoer- en resultaatsecties en de selectielijst.

        Returns
        -------
        str
            Volledige HTML-string geschikt voor QTextBrowser.setHtml().
        """
        titel = package.metadata.project_name or 'Rapport'

        secties: list[str] = []
        for item in package.selected_items:
            if item.kind == 'invoer':
                sec = next(
                    (s for s in package.input_sections if s.id == item.source_ref),
                    None,
                )
            elif item.kind == 'resultaat':
                sec = next(
                    (s for s in package.result_sections if s.id == item.source_ref),
                    None,
                )
            else:
                sec = None
            if sec is not None:
                secties.append(self._sectie_html(sec))

        body = '\n'.join(secties) if secties else '<p class="leeg">Geen secties geselecteerd.</p>'

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

    def _sectie_html(self, sec: ReportSection) -> str:
        """Render één ReportSection als HTML-fragment."""
        delen: list[str] = [f'<h2>{_esc(sec.title)}</h2>']

        if sec.fields:
            delen.append(self._velden_html(sec.fields))

        for tabel in sec.tables:
            delen.append(self._tabel_html(tabel))

        for blok in sec.text_blocks:
            tekst = blok.effective_text
            if tekst:
                delen.append(f'<p class="tekst">{_esc(tekst)}</p>')

        return '\n'.join(delen)

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
        header = ''.join(f'<th>{_esc(k)}</th>' for k in tabel.columns)
        rijen = []
        for i, rij in enumerate(tabel.rows):
            klasse = 'odd' if i % 2 == 0 else 'even'
            cellen = ''.join(f'<td>{_esc(cel)}</td>' for cel in rij)
            rijen.append(f'<tr class="{klasse}">{cellen}</tr>')
        if tabel.title:
            kop = f'<p style="font-size:11px;font-weight:600;color:{_LABEL};margin:8px 0 3px;">{_esc(tabel.title)}</p>'
        else:
            kop = ''
        return f'{kop}<table><tr>{header}</tr>{"".join(rijen)}</table>'


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
