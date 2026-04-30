# Resultaten 3x3 figuurtabel (Msd / Dsd / Urep BGT) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aan de resultaatbeschrijving een nieuwe sectie toevoegen met een 3-kolom × 3-rij figuurtabel: kolommen Msd (rekenmoment, UGT) / Dsd (rekendwarskracht, UGT) / Urep (representatieve verplaatsing, BGT); rij 1 = kop met grootheid + extreme waarde; rij 2 = grafische weergave van de situatie waarin het extremum optreedt; rij 3 = bronfase (welke fase de extreme waarde gaf). Werkt in HTML-preview, WYSIWYG-preview en Word-export.

**Architecture:** Nieuwe builder-methode `_build_extremen_overzicht()` in `ResultDescriptionBuilder` die per resultaattype (moment, shear, displacement) over alle fases en stappen heen de extreme waarde + bronfase + bronstap bepaalt. De sectie krijgt drie `ReportImageRequest`s en een `ReportTable` met de tekstuele rij (kop + bronfase). Voor de figuurrendering wordt een gedeelde helper gebruikt die de bestaande `render_output_charts()` of `SectionRenderer` aanroept met de juiste fase/stap-context. Image-rendering in Word/HTML wordt opgepakt door het werk uit het rapportage-opbouw plan (Plan 1) — dit plan is dus afhankelijk daarvan.

**Tech Stack:** Python (resultaat-extremenbepaling), bestaande chart-renderers, base64-image embedding voor HTML-preview, `python-docx` met inline-shapes voor Word.

---

## Afhankelijkheden

**Vereist eerst:** `docs/superpowers/plans/2026-04-30-rapportage-opbouw-uitbreiding.md` — die plant het algemene mechanisme om afbeeldingen in `ReportSection.images` te renderen via `WordExporter` en `HtmlPreviewBuilder`. Dit plan leunt op die infrastructuur.

Als die infrastructuur er nog niet is bij start van dit plan: voer eerst de relevante taken uit het rapportage-opbouw plan uit (Task 3 + Task 4 daarvan).

---

## Bestandsstructuur

**Te wijzigen bestanden:**
- `reporting/builders/result_description_builder.py` — nieuwe `_build_extremen_overzicht()` methode + aanroep in `build()`
- `reporting/models.py` — eventueel nieuw veld op `ReportImageRequest` (bijv. `result_attr: str | None`) zodat de figuur-renderer weet welk type grafiek nodig is. Of nieuw `figure_key`-waarde-set: `'moment_curve'`, `'shear_curve'`, `'disp_curve'`
- Renderer-helper (gedeeld tussen Word en HTML, zie Plan 1)
- `tests/test_result_description_builder.py` — uitbreiden met test voor de nieuwe sectie

**Niet aanraken:**
- Bestaande `_anchor_forces` en `_per_phase_summary` secties (blijven naast de nieuwe sectie bestaan)

---

## Open vragen voor de gebruiker

**Vraag 1: welke figuur exact?**

Drie kandidaten voor "grafische weergave van de situatie van Msd/Dsd/Urep":

- (a) Moment-/dwarskracht-/verplaatsingsgrafiek over de diepte (de huidige `render_output_charts()`-output) voor de fase + stap waarin het extremum optreedt
- (b) Doorsnedefiguur (`SectionRenderer.render()`) van die fase, met markering van de positie waarin het extremum optreedt
- (c) Combinatie: kleine grafiek + indicatie

**Aanbeveling: (a)** — past bij de aard van de grootheid (verloop over diepte) en is het meest informatief. De huidige `render_output_charts()` rendert al een 3-paneels grafiek (M/D/U); voor deze sectie hebben we drie afzonderlijke single-paneel grafieken nodig.

Bevestig of we (a) doen, en zo ja: moeten alle stappen worden weergegeven (zoals nu), of alleen de stap waarin het extremum optreedt?

**Vraag 2: welke verification_type telt voor "BGT"?**

In de huidige codebase staat in `_VTYPE_VOLGORDE = [4, 5, 0, 1, 3, 14]` met labels 6.1 t/m 6.5. CUR 166 conventie:
- UGT (Msd, Dsd): stap 6.5 (of 6.5 × factor) — meest stringent
- BGT (Urep): stap 6.4 — representatieve verplaatsing

Bevestig welke `verification_type` (of stap-key) als "Msd", "Dsd" en "Urep BGT" gebruikt moet worden, of dat we het maximum over alle UGT-stappen nemen voor Msd/Dsd.

**Vraag 3: kop-rij — wat erin?**

Optie A: alleen grootheid: "Msd" / "Dsd" / "Urep BGT"
Optie B: grootheid + waarde + eenheid: "Msd = 245 kNm/m"
Aanbeveling: B — directer informatief.

**Vraag 4: bronfase-rij — labelvorm**

Optie A: "Fase 3" (alleen nummer)
Optie B: "Fase 3 — Eindsituatie" (nummer + naam)
Aanbeveling: B.

---

## Task 1: Extremenbepaling

**Files:**
- Modify: `reporting/builders/result_description_builder.py`
- Test: `tests/test_result_description_builder.py`

- [ ] **Step 1: TDD — schrijf test voor `_find_extreme(project, attr, vtype_filter)`**

```python
def test_find_extreme_levert_grootste_absolute_waarde():
    """Geeft (waarde, fase_nummer, stap_key, diepte) van max |attr| over alle fases/stappen."""
    project = _mini_project_met_resultaten()
    builder = ResultDescriptionBuilder()
    val, fase, stap, diepte = builder._find_extreme(project, 'moment')
    assert val == pytest.approx(...)
    assert fase == 2
```

- [ ] **Step 2: Implementeer `_find_extreme()`**

```python
def _find_extreme(
    self, project: Project, attr: str, vtype_filter: list[int] | None = None,
) -> tuple[float, int, str, float] | None:
    """Vind absolute extremum over alle fases en stappen.

    Parameters
    ----------
    project: Actief project met result_steps.
    attr: 'moment', 'shear' of 'disp'.
    vtype_filter: Optionele lijst van toegestane verification_types (UGT vs BGT).

    Returns
    -------
    tuple[float, int, str, float] | None
        (waarde, fase_nummer, stap_key, diepte) van het absolute maximum;
        None als er geen data is.
    """
    beste = None
    for sk, step in project.result_steps.items():
        if vtype_filter is not None and step.verification_type not in vtype_filter:
            continue
        for stage_num, rs in step.stages.items():
            ex = self._extremes(rs, attr)
            if ex is None:
                continue
            max_v, max_d, min_v, min_d = ex
            for v, d in [(max_v, max_d), (min_v, min_d)]:
                if beste is None or abs(v) > abs(beste[0]):
                    beste = (v, stage_num, sk, d)
    return beste
```

- [ ] **Step 3: Commit**

---

## Task 2: Sectie-bouw

**Files:**
- Modify: `reporting/builders/result_description_builder.py`

- [ ] **Step 1: Voeg `_build_extremen_overzicht()` toe**

```python
def _build_extremen_overzicht(self, project: Project) -> ReportSection:
    """Bouw de 3x3 figuurtabel met Msd/Dsd/Urep BGT en bronfases."""
    sec = ReportSection(id='extremen_overzicht',
                        title='Maatgevende resultaten')

    # UGT-stappen voor Msd/Dsd; BGT-stap voor Urep — keuze in samenspraak met gebruiker
    UGT_VTYPES = [4, 5, 0, 3, 14]   # 6.1, 6.2, 6.3, 6.5, 6.5×factor
    BGT_VTYPES = [1]                 # 6.4

    msd  = self._find_extreme(project, 'moment', UGT_VTYPES)
    dsd  = self._find_extreme(project, 'shear',  UGT_VTYPES)
    urep = self._find_extreme(project, 'disp',   BGT_VTYPES)

    cols: list[tuple[str, str, tuple | None]] = [
        ('Msd',     'moment_curve', msd),
        ('Dsd',     'shear_curve',  dsd),
        ('Urep BGT','disp_curve',   urep),
    ]

    # Rij 1: kop met waarde
    kop_cellen = []
    for label, _, ex in cols:
        if ex is None:
            kop_cellen.append(label)
        else:
            val, _stage, _step, _depth = ex
            eenheid = {'Msd': 'kNm/m', 'Dsd': 'kN/m', 'Urep BGT': 'mm'}[label]
            kop_cellen.append(f'{label} = {fmt_number(abs(val))} {eenheid}')

    # Rij 2: figuren (geen tekst — komen via images)
    # Rij 3: bronfase
    bron_cellen = []
    for _, _, ex in cols:
        if ex is None:
            bron_cellen.append('—')
        else:
            _val, stage_num, _step, _depth = ex
            bron_cellen.append(self._stage_naam(project, stage_num))

    sec.tables.append(ReportTable(
        id='extremen_kop_en_bronfase',
        title='',
        columns=kop_cellen,
        rows=[bron_cellen],
    ))

    # Figuren als ReportImageRequest — exporters renderen ze
    for label, fig_key, ex in cols:
        if ex is None:
            continue
        _val, stage_num, step_key, _depth = ex
        sec.images.append(ReportImageRequest(
            id=f'extreme_{label.lower().replace(" ", "_")}',
            caption=f'{label} — fase {stage_num}, stap {_step_short_label(step_key)}',
            figure_key=fig_key,
            stage_index=stage_num - 1,
            step_key=step_key,
        ))
    return sec
```

- [ ] **Step 2: Roep aan in `build()`**

```python
def build(self, project, stage_index, step_key, overrides=None):
    sections = []
    sections.append(self._anchor_forces(project))
    sections.append(self._per_phase_summary(project))
    sections.append(self._build_extremen_overzicht(project))
    return sections
```

- [ ] **Step 3: Commit**

---

## Task 3: Renderer-koppeling — figure_keys honoreren

**Files:**
- Modify: rendererhelper uit Plan 1 (gedeeld tussen `WordExporter` en `HtmlPreviewBuilder`)

- [ ] **Step 1: Voeg `figure_key`-handlers toe**

`'cross_section'` → `SectionRenderer.render()` voor `stage_index`
`'moment_curve'`  → render alleen het moment-paneel uit `render_output_charts()`
`'shear_curve'`   → idem voor dwarskracht
`'disp_curve'`    → idem voor verplaatsing

Aanbeveling: voeg een functie `render_single_chart(project, stage_index, step_key, attr)` toe in `renderers/output_charts.py` die één paneel rendert, zodat `_render_figure()` kan kiezen welke render-methode te gebruiken op basis van `figure_key`.

- [ ] **Step 2: Test in HTML-preview en Word-export end-to-end**

- [ ] **Step 3: Commit**

---

## Task 4: Layout — 3x3 in HTML en Word

**Files:**
- Modify: `reporting/builders/html_preview_builder.py`
- Modify: `exporters/word_exporter.py`

De huidige aanpak met losse `images` en losse `tables` levert: tabel met kop + bronfase, gevolgd door drie afbeeldingen vertikaal. Voor een echte 3-kolom layout in HTML én Word moet rendering gegroepeerd worden.

**Aanbevolen aanpak:** voeg een `inline=True`-vlag toe aan `ReportImageRequest` of een nieuw `ReportImageGroup`-type dat een rij van afbeeldingen voorstelt. In de exporter:
- HTML: render als `<table><tr><th>kop1</th>…</tr><tr><td><img></td>…</tr><tr><td>bronfase</td>…</tr></table>`
- Word: gebruik een 3x3 docx-tabel; rij 1 tekst, rij 2 elke cel een `add_picture` (resized), rij 3 tekst

- [ ] **Step 1: Modelwijziging** — voeg `ReportImageGroup` toe of `inline_row: int | None` op `ReportImageRequest`. Beslis na overleg met gebruiker.

- [ ] **Step 2: Implementeer 3-kolom rendering** in beide exporters. Test visueel.

- [ ] **Step 3: Commit**

---

## Task 5: Handmatige rooktest

- [ ] App starten, project met UGT- én BGT-resultaten laden
- [ ] Rapportage-tab → Selectie: nieuwe item "Maatgevende resultaten" verschijnt onder resultaat
- [ ] HTML-preview: 3x3 tabel met titels, figuren, bronfases
- [ ] Word WYSIWYG-preview: idem, in echte docx-tabel
- [ ] Verifieer waarden tegen handmatige inspectie van Debug-tab voor extremen

---

## Acceptatiecriteria

- Sectie "Maatgevende resultaten" verschijnt automatisch in `auto_populate_plan` (kind 'resultaat')
- 3 kolommen: Msd / Dsd / Urep BGT
- 3 rijen: titel-met-waarde / figuur / bronfase
- HTML-preview en Word-export tonen dezelfde 3x3 layout
- Tests slagen, inclusief minstens één test op `_find_extreme` met deterministische data

## Bekende beperkingen

- Vereist dat Plan 1 (`rapportage-opbouw-uitbreiding`) Task 3 + 4 (Word/HTML image-rendering) eerst zijn uitgevoerd
- Aanname dat extremen "absoluut max" zijn over alle fases — als gebruiker een andere selectie wil (bijv. alleen positief moment, of per fase een eigen 3x3) is dat een aparte iteratie
