# Rapportage-opbouw uitbreiding — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** De rapportage-selectielijst uitbreiden zodat een volledig basisrapport wordt opgebouwd in vaste volgorde — Invoerbeschrijving (incl. damwandgegevens, geometrie/afbeelding per fase, waterpeilen en actieve ondersteuningen) → Grondsoortentabellen → Resultaatbeschrijving — en de Word-export afbeeldingen kan renderen zodat het in zowel HTML-preview als WYSIWYG-preview en de Word-uitvoer correct verschijnt.

**Architecture:** Drie wijzigingen op de bestaande pijplijn. (1) `auto_populate_plan` voegt expliciet damwand-secties toe en garandeert de volgorde damwand → invoer per fase → grondsoorten → resultaat. (2) `WordExporter` krijgt image-support (zoals `WordHoofdstukExporter` al heeft), zodat doorsnedefiguren per fase in Word terechtkomen. (3) `HtmlPreviewBuilder` rendert ook de figuren als `<img>`-tag, zodat de HTML-preview consistent is.

**Tech Stack:** Python, `python-docx` (incl. `docx.shared.Cm` voor figuurgrootte), bestaande `SectionRenderer` voor figuurrendering, base64-image-embedding voor HTML-preview.

---

## Bestandsstructuur

**Te wijzigen bestanden:**
- `app/report_controller.py` — `auto_populate_plan()` + `build_package()` aanpassen
- `reporting/builders/damwand_hoofdstuk_builder.py` — publieke `build()` toevoegen die alle secties retourneert (intern reeds `_bouw_damwand_sectie`/`_bouw_fase_secties`)
- `exporters/word_exporter.py` — `_write_section()` uitbreiden om `section.images` te renderen (zoals `WordHoofdstukExporter._schrijf_figuur` al doet)
- `reporting/builders/html_preview_builder.py` — `_sectie_html()` uitbreiden om `<img>`-tags voor `section.images` te emitteren
- `reporting/builders/input_description_builder.py` — fase-secties moeten een `ReportImageRequest` voor de doorsnedefiguur bevatten (figure_key='cross_section' of vergelijkbaar)
- `tests/test_word_exporter.py` (nieuw of uitgebreid) — verifieer dat afbeeldingen in een sectie tot een `inline_shape` in het docx leiden

**Niet aanraken:**
- `WordHoofdstukExporter` (blijft het figuur-pad voor het damwand-only export-pad)
- `tab_aanvullende_berekeningen.py` (komt in een latere iteratie)
- Debug-tab (komt nooit in rapportage)

---

## Open vragen voor de gebruiker

**Vraag 1: figuur per fase — welke?**
- Optie A: De doorsnede (cross-section) gerenderd voor die specifieke fase, met grondlagen, waterstanden en actieve ondersteuningen. Bestaand renderpad: `SectionRenderer.render()`.
- Optie B: Alleen een vereenvoudigde geometrieschets.
- Aanbeveling: A — sluit aan bij wat de Doorsnede-tab al toont.

**Vraag 2: damwandgegevens — eigen sectie of vooraan in fase 1?**
- Optie A: Eigen sectie "Damwandgegevens" als eerste invoerblok (huidige `_bouw_damwand_sectie`).
- Optie B: Inline in fase 1.
- Aanbeveling: A — leesbaarder en sluit aan bij `DamwandHoofdstukBuilder`.

**Vraag 3: figuurgrootte in Word**
- Voorstel: 16 cm breed (past binnen A4-marges).

---

## Task 1: Damwand-builder publieke API

**Files:**
- Modify: `reporting/builders/damwand_hoofdstuk_builder.py`

- [ ] **Step 1: Voeg `build(project)` toe aan `DamwandHoofdstukBuilder`**

```python
def build(self, project: Project) -> list[ReportSection]:
    """Bouw de damwand-secties (gegevens + per-fase invoer met figuren).

    Returns
    -------
    list[ReportSection]
        Damwandgegevens als eerste sectie, gevolgd door één sectie per fase.
    """
    secties: list[ReportSection] = [self._bouw_damwand_sectie(project)]
    secties.extend(self._bouw_fase_secties(project))
    return secties
```

- [ ] **Step 2: Schrijf een unit-test in `tests/test_damwand_hoofdstuk_builder.py`** die controleert dat `build()` een niet-lege lijst geeft voor een minimaal project en dat de eerste sectie de id `damwand_gegevens` heeft.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: publieke build() op DamwandHoofdstukBuilder"
```

---

## Task 2: ReportController integreren

**Files:**
- Modify: `app/report_controller.py`

- [ ] **Step 1: Voeg `build_damwand_sections()` toe**

```python
def build_damwand_sections(self) -> list[ReportSection]:
    """Bouw damwandsecties (gegevens + per-fase invoer met figuren)."""
    project = self._app.get_active_project()
    if not project:
        return []
    return self._damwand_builder.build(project)
```

en voeg `from reporting.builders.damwand_hoofdstuk_builder import DamwandHoofdstukBuilder` toe + `self._damwand_builder = DamwandHoofdstukBuilder()` in `__init__`.

- [ ] **Step 2: Pas `auto_populate_plan()` aan voor de nieuwe volgorde**

```python
def auto_populate_plan(self) -> None:
    """Vul het rapportplan in vaste volgorde: damwand → invoer → grondsoorten → resultaat."""
    from reporting.models import ReportItem
    damwand_secs = self.build_damwand_sections()
    soil_secs = self.build_soil_sections()
    result_secs = self.build_result_descriptions()

    for sec in damwand_secs:
        self._report.plan.add_item(ReportItem(
            id=f'damwand_{sec.id}', kind='invoer',
            caption=sec.title, source_ref=sec.id,
        ))
    for sec in soil_secs:
        self._report.plan.add_item(ReportItem(
            id=f'grondsoorten_{sec.id}', kind='grondsoorten',
            caption=sec.title, source_ref=sec.id,
        ))
    for sec in result_secs:
        self._report.plan.add_item(ReportItem(
            id=f'result_{sec.id}', kind='resultaat',
            caption=sec.title, source_ref=sec.id,
        ))
```

NB: De oude losse `input_secs`-loop (`InputDescriptionBuilder.build`) vervalt — alle invoer komt nu via `DamwandHoofdstukBuilder`. Verifieer dat `InputDescriptionBuilder.build()` niet ergens anders wordt aangeroepen vóór je het uit `auto_populate_plan` haalt.

- [ ] **Step 3: Pas `build_package()` aan**

`input_sections=` moet de damwand-secties bevatten, niet meer de output van `build_input_descriptions()`. Deze worden tóch door bestaande tabs gebruikt (`Invoerbeschrijving`-tab) — controleer eerst of `build_input_descriptions()` nog elders nodig is. Zo ja: laat die methode bestaan, maar gebruik in `build_package` de damwand-secties.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: damwand-secties in auto_populate_plan + vaste volgorde"
```

---

## Task 3: WordExporter — afbeeldingen ondersteunen

**Files:**
- Modify: `exporters/word_exporter.py`
- Test: `tests/test_word_exporter.py`

- [ ] **Step 1: TDD — schrijf test die controleert dat een sectie met `images=[...]` tot een `inline_shape` leidt**

```python
def test_word_exporter_writes_image_for_section(tmp_path):
    """Een ReportSection met images moet een inline_shape in de docx geven."""
    from reporting.models import (ReportPackage, ReportSection,
                                   ReportImageRequest, ReportItem, ReportMetadata)
    from exporters.word_exporter import WordExporter
    from docx import Document

    sec = ReportSection(
        id='fase_1', title='Fase 1',
        images=[ReportImageRequest(
            id='img_fase_1', caption='Doorsnede fase 1',
            figure_key='cross_section', stage_index=0, step_key=None,
        )],
    )
    pkg = ReportPackage(
        metadata=ReportMetadata(project_name='T'),
        input_sections=[sec],
        selected_items=[ReportItem(id='input_fase_1', kind='invoer',
                                     caption='Fase 1', source_ref='fase_1')],
    )
    out = tmp_path / 'out.docx'
    err = WordExporter().export(pkg, None, str(out), project=...)  # zie Step 2
    assert err is None
    doc = Document(str(out))
    assert len(doc.inline_shapes) >= 1
```

- [ ] **Step 2: Pas de `export()`-signatuur aan om `project` te accepteren** (voor figuurrendering). Zo niet, importeer `project` via een meegegeven render-callback of via `ReportPackage`. Aanbeveling: voeg `project: Project | None = None` toe aan `export()` en pas `ReportController.export_word()` aan.

- [ ] **Step 3: Voeg `_write_image()` toe aan `WordExporter`** (kopieer uit `WordHoofdstukExporter._schrijf_figuur` / `_render_figuur`):

```python
def _write_image(self, doc, img_req: ReportImageRequest, project) -> None:
    """Render figuur en voeg toe als inline shape."""
    from io import BytesIO
    from docx.shared import Cm
    if project is None:
        return
    png_bytes = self._render_figure(img_req, project)
    if not png_bytes:
        return
    doc.add_picture(BytesIO(png_bytes), width=Cm(16))
    if img_req.caption:
        doc.add_paragraph(img_req.caption, style='Caption')

def _render_figure(self, img_req: ReportImageRequest, project) -> bytes | None:
    """Render een figuur naar PNG-bytes; gebruik figure_key voor type-keuze."""
    # Hergebruik logica uit WordHoofdstukExporter._render_figuur — extraheer
    # eventueel naar utils/figure_renderer.py voor DRY.
    ...
```

- [ ] **Step 4: Roep `_write_image()` aan in `_write_section()`** voor elke `img_req` in `section.images`.

- [ ] **Step 5: Commit**

---

## Task 4: HtmlPreviewBuilder — afbeeldingen renderen

**Files:**
- Modify: `reporting/builders/html_preview_builder.py`

- [ ] **Step 1: Voeg figuurrendering toe in `_sectie_html()`** — embed PNG als base64 data-URI zodat geen tijdelijke bestanden nodig zijn:

```python
import base64

def _figuur_html(self, img_req, project) -> str:
    if project is None:
        return ''
    png = render_figure(img_req, project)  # gedeelde helper
    if not png:
        return ''
    b64 = base64.b64encode(png).decode('ascii')
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="max-width:100%; margin:8px 0;">'
        + (f'<p style="font-size:10px;color:#666;">{_esc(img_req.caption)}</p>'
           if img_req.caption else '')
    )
```

- [ ] **Step 2:** Pas `HtmlPreviewBuilder.build()` aan om `project` te ontvangen, en update aanroep in `app/main_window.py:_update_preview()` zodat het actieve project wordt doorgegeven.

- [ ] **Step 3: Commit**

---

## Task 5: InputDescriptionBuilder — figuurverzoeken in fase-secties

**Files:**
- Modify: `reporting/builders/damwand_hoofdstuk_builder.py` (waar fase-secties gebouwd worden)

- [ ] **Step 1:** In `_bouw_fase_secties()`, voeg per fase een `ReportImageRequest` toe:

```python
sec.images.append(ReportImageRequest(
    id=f'fig_fase_{i + 1}',
    caption=f'Doorsnede fase {i + 1}: {kaart.stage_name}',
    figure_key='cross_section',
    stage_index=i,
    step_key=None,
))
```

- [ ] **Step 2: Commit**

---

## Task 6: Handmatige rooktest

- [ ] App starten, project laden
- [ ] Rapportage-tab → Selectie: controleer volgorde damwand → grondsoorten → resultaat
- [ ] HTML-preview: doorsnedefiguren per fase moeten zichtbaar zijn
- [ ] Word WYSIWYG-preview: idem, met grondsoorten-tabel(len) en resultatenoverzicht
- [ ] Word-export naar `.docx`: open in Word, controleer figuren en stijlen

---

## Acceptatiecriteria

- `auto_populate_plan` levert items in volgorde: damwand-gegevens → fase 1, 2, … → grondsoortentabellen → resultaat
- Elke fase-sectie bevat een doorsnedefiguur die in HTML-preview én Word-export verschijnt
- Bestaande tests blijven slagen
- `docx2pdf` (WYSIWYG-preview) toont een complete PDF met figuren

## Bekende beperkingen

- Aanvullende berekeningen (verticaal evenwicht, hydraulische grondbreuk) komen in een latere iteratie
- Debug-tab wordt nooit opgenomen
- Cache-management voor figuren (om herrenders bij elke selectie-wijziging te voorkomen) is geen onderdeel — als performance een probleem wordt: extraheer naar volgende iteratie
