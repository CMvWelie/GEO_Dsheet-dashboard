# Ontwerp: Damwand Hoofdstuk Word-export

**Datum:** 2026-04-16
**Status:** Goedgekeurd
**Scope:** Deel A — invoergegevens en resultaten (geen sterktechecks)

---

## Doel

Een "Exporteer rapport"-knop die voor het actieve D-Sheet project een volledig Word-document genereert met één damwandhoofdstuk. De opmaak wordt bepaald door een stijlentemplate (`templates/damwand_stijlen.docx`); de inhoud wordt volledig programmatisch opgebouwd.

Deel B (NEN-EN 1993-5 sterktechecks, corrosie, γM-factoren) volgt in een later stadium als uitbreiding op dezelfde builder.

---

## Hoofdstukstructuur

| # | Sectie | Inhoud |
|---|--------|--------|
| 1 | Grondlagen | Tabel per profiel (links en rechts): naam, bovenzijde [m NAP], onderzijde [m NAP], γdr, γnat, c, φ, δ, kh1, kh2, kh3 |
| 2 | Damwandgegevens | Profielnaam, staalkwaliteit, hoogte [mm], breedte [mm], EI [kNm²/m], Wy;el [cm³/m], opneembaar moment [kNm/m], kopniveau [m NAP], teenniveau [m NAP], lengte [m] |
| 3 | Invoer per fase | Per constructiefase: maaiveld links/rechts, waterpeilen, actieve ondersteuningen (naam + niveau), actieve belastingen; gevolgd door een headless dwarsdoorsnede-figuur van die fase |
| 4 | Resultaten per fase | Conclusietabel alle fases: max \|M\| [kNm/m], max \|V\| [kN/m], max \|u\| [mm], mob. moment [%], mob. grond [%], ankerkrachten (naam + kracht [kN/m]) |
| 5 | Resultatengrafieken | Moment- en dwarskrachtgrafiek van de maatgevende resultaatstap (ULS); vervormingsgrafiek van resultaatstap "6.5" (CUR166 §6.5, SLS/karakteristiek) |

---

## Architectuur

### Nieuwe componenten

#### `reporting/builders/damwand_hoofdstuk_builder.py` — `DamwandHoofdstukBuilder`

Orchestreert bestaande builders in volgorde. Accepteert het actieve `Project`, de maatgevende `step_key` (ULS) en de verplaatsingsstap `disp_step_key` ("6.5"). Geeft een `list[ReportSection]` terug.

```
build(project, governing_step_key, disp_step_key) -> list[ReportSection]
    1. SoilTableBuilder.build_soil_table()          → sectie 1
    2. InputDescriptionBuilder._sheet_piling()      → sectie 2
    3. InputDescriptionBuilder.build_all_stages()   → secties 3 (met ReportImageRequest per fase)
    4. ResultDescriptionBuilder._per_phase_summary()→ sectie 4
    5. ReportImageRequest(grafieken)                → sectie 5
```

`ReportImageRequest` in sectie 3 gebruikt `figure_key='section'` met `stage_index` per fase.
`ReportImageRequest` in sectie 5 gebruikt `figure_key='results_uls'` en `figure_key='results_disp'`.

#### `exporters/word_hoofdstuk_exporter.py` — `WordHoofdstukExporter`

Geen Qt-imports. Accepteert `list[ReportSection]`, `ReportMetadata`, `Project` en paden naar template en outputbestand.

Verantwoordelijkheden:
- Opent `templates/damwand_stijlen.docx` als basis
- Schrijft per sectie: Heading 2 (sectietitel), veldenlijst of datatabel, tekst
- Rendert figuren headless via `FigureCanvasAgg` naar PNG-bytes en voegt in als inline afbeelding
- Figuurrendering delegeert naar `SectionRenderer.render()` en `render_output_charts()` — beide al aanwezig

Figuurafmetingen: doorsnede 16×12 cm, resultatengrafieken 16×8 cm per grafiek.

#### `templates/damwand_stijlen.docx`

Leeg Word-document met uitsluitend stijldefinities:
- `Heading 1` — hoofdstuktitel
- `Heading 2` — sectietitel
- `DKIB Tabel` — tabelstijl voor datatables
- Standaard lettertype, marges, paginaformaat (A4)

Geen inhoud, geen placeholders. python-docx opent dit als `Document('templates/damwand_stijlen.docx')` en voegt alle content programmatisch toe.

#### Export-knop in de UI

Nieuwe knop "Exporteer rapport (Word)" in `main_window.py`, zichtbaar buiten de tab-structuur (bijv. in een toolbar of onderaan het hoofdvenster). Altijd actief zodra een project geladen is.

Handler `_on_export_hoofdstuk()`:
1. Haal actief project op uit `AppState`
2. Bepaal `governing_step_key`: eerste ULS-stap in `project.result_steps`, of via een keuzevenster als meerdere beschikbaar
3. Bepaal `disp_step_key`: zoek op sleutel die "6.5" bevat in `project.result_steps`; toon waarschuwing als niet gevonden
4. Roep `DamwandHoofdstukBuilder.build()` aan
5. Open `QFileDialog` voor opslaan
6. Roep `WordHoofdstukExporter.export()` aan
7. Toon succesbericht of `QMessageBox.warning()` bij fout

---

## Data-flow

```
AppState.projects[active]
    │
    ▼
DamwandHoofdstukBuilder.build(project, governing_step_key, disp_step_key)
    ├── SoilTableBuilder          → ReportSection (grondlagen)
    ├── InputDescriptionBuilder   → ReportSection (damwand)
    ├── InputDescriptionBuilder   → list[ReportSection] (fases + ReportImageRequest per fase)
    ├── ResultDescriptionBuilder  → ReportSection (conclusietabel)
    └── ReportImageRequest ×2     → ReportSection (grafieken ULS + 6.5)
    │
    ▼
list[ReportSection]
    │
    ▼
WordHoofdstukExporter.export(sections, metadata, project, template_path, output_path)
    ├── Document('templates/damwand_stijlen.docx')
    ├── per sectie: schrijf titels, tabellen, tekst
    ├── per ReportImageRequest: render headless → PNG-bytes → inline afbeelding
    └── document.save(output_path)
```

---

## Ontwerpbeslissingen

| Beslissing | Keuze | Reden |
|------------|-------|-------|
| Template aanpak | Stijlentemplate (.docx) | Opmaak aanpasbaar zonder code; huisstijl DKIB |
| Figuurrendering | Headless via FigureCanvasAgg in exporter | Geen Qt nodig in exporter; bestaande renderers hergebruikt |
| Maatgevende stap | Configureerbaar via `governing_step_key` | Projecten kunnen wisselende stapnamen hebben |
| Verplaatsingsstap | Zoek op "6.5" in stapnaam | CUR166 §6.5 is vaste conventie; waarschuwing als afwezig |
| Meerdere doorsneden | Niet in scope (uitbreiding later) | Begin eenvoudig; architectuur laat uitbreiding toe |
| Deel B (sterktechecks) | Niet in scope | Aparte iteratie; builder is uitbreidbaar |

---

## Uitbreidingspunten (toekomst)

- **Meerdere doorsneden**: `DamwandHoofdstukBuilder` accepteert `list[Project]` en genereert kolommen per doorsnede in de conclusietabel
- **Deel B**: Nieuwe `SterkteToetsingBuilder` voegt secties 6–9 toe (dwarskracht-UC, plooi-UC, moment-UC, knik-UC) — vereist extra invoervelden (corrosie, RC-klasse, β-factoren)
- **Meerdere templates**: `template_path` is configureerbaar via `ConfigManager`
