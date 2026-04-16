# Damwand Hoofdstuk Word-export — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Een "Exporteer rapport (Word)" knop die voor het actieve project een Word-document genereert met vijf secties: grondlagen, damwandgegevens, invoer per fase (+ doorsnede figuren), conclusietabel per fase, en resultatengrafieken.

**Architecture:** `DamwandHoofdstukBuilder` orchestreert bestaande builders en retourneert een `list[ReportSection]`. `WordHoofdstukExporter` opent een `.docx` stijlentemplate, schrijft secties en rendert figuren headless via `FigureCanvasAgg`. Een knop in `main_window.py` verbindt alles via `QFileDialog`.

**Tech Stack:** python-docx, matplotlib (`FigureCanvasAgg`), PyQt6 (alleen `main_window.py`), bestaande `SoilTableBuilder`, `InputDescriptionBuilder`, `OutputRenderer`, `SectionRenderer`.

---

## Bestandskaart

| Actie | Pad | Verantwoordelijkheid |
|-------|-----|----------------------|
| Nieuw | `reporting/builders/damwand_hoofdstuk_builder.py` | Sectie-opbouw: orchestratie van alle vijf secties |
| Nieuw | `exporters/word_hoofdstuk_exporter.py` | Template openen, secties schrijven, figuren renderen |
| Nieuw | `templates/damwand_stijlen.docx` | Stijlentemplate (aangemaakt door Task 5) |
| Nieuw | `tests/test_damwand_hoofdstuk_builder.py` | Unit-tests voor de builder |
| Nieuw | `tests/test_word_hoofdstuk_exporter.py` | Unit-tests voor de exporter |
| Wijzig | `app/main_window.py` | Export-knop + handler `_on_export_hoofdstuk()` |

---

## Task 1: DamwandHoofdstukBuilder — damwandgegevens sectie

**Files:**
- Create: `reporting/builders/damwand_hoofdstuk_builder.py`
- Create: `tests/test_damwand_hoofdstuk_builder.py`

- [ ] **Stap 1: Schrijf de falende test**

`tests/test_damwand_hoofdstuk_builder.py`:
```python
"""Tests voor DamwandHoofdstukBuilder."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.models import (
    Project, FileBundle, SheetPilingElement,
    Soil, SoilProfile, SoilLayer, Stage, ResultSummary,
    ResultStep, ResultStage, ResultPoint,
)
from reporting.builders.damwand_hoofdstuk_builder import DamwandHoofdstukBuilder


def _basis_project(**kwargs) -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        **kwargs,
    )


def _wall() -> SheetPilingElement:
    return SheetPilingElement(
        name='AZ 14-700 (S240GP)',
        x=0.0,
        bottom=-13.5,
        top=-4.3,
        width=1.4,
        height_mm=316.0,
        pile_width_mm=1400.0,
        ei_knm2_per_m=46599.0,
        section_area_cm2=146.1,
        resisting_moment_cm3=1405.0,
        max_char_moment_knm=337.2,
        opneembaar_moment_knm=225.0,
        steel_quality='S240GP',
    )


def test_damwand_sectie_aanwezig() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    secties = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    assert secties.id == 'damwand_gegevens'


def test_damwand_sectie_bevat_profiel_veld() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    sleutels = {f.key for f in sec.fields}
    assert 'profiel' in sleutels


def test_damwand_sectie_bevat_ei_en_opneembaar_moment() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    sleutels = {f.key for f in sec.fields}
    assert 'ei_knm2' in sleutels
    assert 'opneembaar_moment' in sleutels


def test_damwand_sectie_lengte_correct() -> None:
    project = _basis_project(sheet_piling=[_wall()])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    veld = next(f for f in sec.fields if f.key == 'lengte')
    assert '9' in veld.value   # abs(-4.3 - -13.5) = 9.2 m


def test_damwand_sectie_geen_damwand_geeft_lege_fields() -> None:
    project = _basis_project(sheet_piling=[])
    sec = DamwandHoofdstukBuilder()._bouw_damwand_sectie(project)
    assert sec.fields == []
```

- [ ] **Stap 2: Laat de test falen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py -v
```
Verwacht: `ImportError: No module named 'reporting.builders.damwand_hoofdstuk_builder'`

- [ ] **Stap 3: Implementeer de builder met `_bouw_damwand_sectie`**

`reporting/builders/damwand_hoofdstuk_builder.py`:
```python
"""DamwandHoofdstukBuilder — bouwt het volledige damwand-rapportagehoofdstuk."""
from __future__ import annotations
import re

from parsers.models import Project, Stage
from reporting.models import ReportSection, ReportField, ReportTable, ReportImageRequest
from reporting.builders.soil_table_builder import SoilTableBuilder
from reporting.builders.input_description_builder import InputDescriptionBuilder
from utils.formatting import fmt_number


def _find(lst, name: str):
    return next((x for x in (lst or []) if x.name == name), None)


class DamwandHoofdstukBuilder:
    """Bouwt alle vijf secties van het damwand-rapportagehoofdstuk."""

    # ------------------------------------------------------------------
    # Sectie 2: Damwandgegevens
    # ------------------------------------------------------------------

    def _bouw_damwand_sectie(self, project: Project) -> ReportSection:
        """Bouw sectie met profieleigenschappen van de damwand."""
        sec = ReportSection(id='damwand_gegevens', title='Damwandgegevens')
        if not project.sheet_piling:
            return sec
        w = project.sheet_piling[0]
        profiel_naam = re.sub(r'\s*\([^)]+\)\s*$', '', w.name).strip()
        lengte = abs((w.top or 0.0) - w.bottom)
        sec.fields = [
            ReportField('profiel',            'Profiel',                   profiel_naam),
            ReportField('staalkwaliteit',     'Staalkwaliteit',             w.steel_quality),
            ReportField('hoogte_mm',          'Hoogte',                     fmt_number(w.height_mm),        'mm'),
            ReportField('breedte_mm',         'Breedte',                    fmt_number(w.pile_width_mm),    'mm'),
            ReportField('ei_knm2',            'Buigstijfheid EI',           fmt_number(w.ei_knm2_per_m),   'kNm²/m'),
            ReportField('wel_cm3',            'Weerstandsmoment Wy;el',     fmt_number(w.resisting_moment_cm3), 'cm³/m'),
            ReportField('opneembaar_moment',  'Opneembaar moment',          fmt_number(w.opneembaar_moment_knm), 'kNm/m'),
            ReportField('kopniveau',          'Kopniveau',                  fmt_number(w.top) if w.top is not None else '-', 'm NAP'),
            ReportField('teenniveau',         'Teenniveau',                 fmt_number(w.bottom),           'm NAP'),
            ReportField('lengte',             'Lengte',                     fmt_number(lengte),             'm'),
        ]
        return sec
```

- [ ] **Stap 4: Tests laten slagen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py -v
```
Verwacht: alle 5 tests PASS

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/damwand_hoofdstuk_builder.py tests/test_damwand_hoofdstuk_builder.py
git commit -m "feat: voeg DamwandHoofdstukBuilder toe met damwandgegevens-sectie"
```

---

## Task 2: DamwandHoofdstukBuilder — invoer per fase sectie

**Files:**
- Modify: `reporting/builders/damwand_hoofdstuk_builder.py`
- Modify: `tests/test_damwand_hoofdstuk_builder.py`

- [ ] **Stap 1: Schrijf de falende tests**

Voeg toe aan `tests/test_damwand_hoofdstuk_builder.py`:
```python
def _maak_stage(naam: str) -> Stage:
    return Stage(name=naam, left_surface='MV', right_surface='MV',
                 left_water='GWS', right_water='GWS',
                 left_profile='Links', right_profile='Rechts')


def test_fase_secties_één_per_fase() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1'), _maak_stage('Fase 2')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert len(secties) == 2


def test_fase_sectie_id_bevat_fasenummer() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert 'fase_1' in secties[0].id


def test_fase_sectie_bevat_image_request() -> None:
    project = _basis_project(stages=[_maak_stage('Fase 1')])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert len(secties[0].images) == 1
    assert secties[0].images[0].figure_key == 'section'
    assert secties[0].images[0].stage_index == 0


def test_fase_secties_leeg_project() -> None:
    project = _basis_project(stages=[])
    secties = DamwandHoofdstukBuilder()._bouw_fase_secties(project)
    assert secties == []
```

- [ ] **Stap 2: Laat de tests falen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py::test_fase_secties_één_per_fase -v
```
Verwacht: `AttributeError: 'DamwandHoofdstukBuilder' object has no attribute '_bouw_fase_secties'`

- [ ] **Stap 3: Implementeer `_bouw_fase_secties`**

Voeg toe aan `DamwandHoofdstukBuilder` in `reporting/builders/damwand_hoofdstuk_builder.py`:
```python
    # ------------------------------------------------------------------
    # Sectie 3: Invoer per fase
    # ------------------------------------------------------------------

    def _bouw_fase_secties(self, project: Project) -> list[ReportSection]:
        """Bouw één ReportSection per constructiefase, inclusief een figuurverzoek."""
        idb = InputDescriptionBuilder()
        kaarten = idb.build_all_stages(project)
        secties: list[ReportSection] = []
        for i, kaart in enumerate(kaarten):
            sec = ReportSection(
                id=f'fase_{i + 1}_invoer',
                title=f'Fase {kaart.fase_num}: {kaart.stage_name}',
            )
            for rij in kaart.rows:
                sec.fields.append(ReportField(
                    key=f'fase_{i + 1}_{rij.label.lower().replace(" ", "_")}',
                    label=rij.label,
                    value=rij.value,
                    unit=rij.extra,
                ))
            sec.images.append(ReportImageRequest(
                id=f'fase_{i + 1}_doorsnede',
                caption=f'Dwarsdoorsnede fase {kaart.fase_num}',
                figure_key='section',
                stage_index=i,
                step_key=None,
            ))
            secties.append(sec)
        return secties
```

- [ ] **Stap 4: Tests laten slagen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py -v
```
Verwacht: alle tests PASS

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/damwand_hoofdstuk_builder.py tests/test_damwand_hoofdstuk_builder.py
git commit -m "feat: voeg fase-invoer secties toe aan DamwandHoofdstukBuilder"
```

---

## Task 3: DamwandHoofdstukBuilder — conclusietabel + grafieken + build()

**Files:**
- Modify: `reporting/builders/damwand_hoofdstuk_builder.py`
- Modify: `tests/test_damwand_hoofdstuk_builder.py`

- [ ] **Stap 1: Schrijf de falende tests**

Voeg toe aan `tests/test_damwand_hoofdstuk_builder.py`:
```python
from parsers.models import ResultSummary


def _maak_summary(stage_nr: int, moment: float = 100.0) -> ResultSummary:
    return ResultSummary(
        stage_number=stage_nr,
        max_moment_knm=moment,
        max_shear_kn=80.0,
        max_disp_mm=30.0,
        mob_moment_pct=75.0,
        mob_grond_pct=70.0,
        ondersteuningen=[('Anker A', 120.0, -8.5)],
    )


def test_conclusietabel_sectie_id() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert sec.id == 'conclusietabel'


def test_conclusietabel_bevat_tabel() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1), _maak_summary(2)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert len(sec.tables) == 1
    assert len(sec.tables[0].rows) == 2


def test_conclusietabel_kolommen() -> None:
    project = _basis_project(result_summaries=[_maak_summary(1)])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    kolommen = sec.tables[0].columns
    assert 'Fase' in kolommen[0]
    assert 'kNm' in kolommen[1]


def test_conclusietabel_lege_summaries() -> None:
    project = _basis_project(result_summaries=[])
    sec = DamwandHoofdstukBuilder()._bouw_conclusietabel(project)
    assert sec.tables == []


def test_grafiek_secties_bevatten_twee_image_requests() -> None:
    project = _basis_project(
        stages=[_maak_stage('F1')],
        result_summaries=[_maak_summary(1)],
    )
    secties = DamwandHoofdstukBuilder()._bouw_grafiek_secties(
        project, governing_step_key='ULS', disp_step_key='6.5'
    )
    alle_images = [img for sec in secties for img in sec.images]
    figuur_keys = {img.figure_key for img in alle_images}
    assert 'moment_shear' in figuur_keys
    assert 'displacement' in figuur_keys


def test_build_geeft_vijf_sectiegroepenblokken() -> None:
    project = _basis_project(
        sheet_piling=[_wall()],
        stages=[_maak_stage('F1')],
        result_summaries=[_maak_summary(1)],
    )
    secties = DamwandHoofdstukBuilder().build(
        project, governing_step_key='ULS', disp_step_key='6.5'
    )
    ids = [s.id for s in secties]
    # Minstens: grondlagen (0+), damwand, fase_1_invoer, conclusietabel, grafieken
    assert 'damwand_gegevens' in ids
    assert 'fase_1_invoer' in ids
    assert 'conclusietabel' in ids
```

- [ ] **Stap 2: Laat de tests falen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py::test_conclusietabel_sectie_id -v
```
Verwacht: `AttributeError`

- [ ] **Stap 3: Implementeer `_bouw_conclusietabel`, `_bouw_grafiek_secties`, `_governing_stage_index` en `build()`**

Voeg toe aan `DamwandHoofdstukBuilder`:
```python
    # ------------------------------------------------------------------
    # Sectie 4: Conclusietabel per fase
    # ------------------------------------------------------------------

    def _bouw_conclusietabel(self, project: Project) -> ReportSection:
        """Bouw conclusietabel met resultaten per fase."""
        sec = ReportSection(id='conclusietabel', title='Resultaten per fase')
        if not project.result_summaries:
            return sec
        kolommen = [
            'Fase', 'Max |M| [kNm/m]', 'Max |V| [kN/m]',
            'Max |u| [mm]', 'Mob. moment [%]', 'Mob. grond [%]',
        ]
        rijen: list[list[str]] = []
        for rs in sorted(project.result_summaries, key=lambda r: r.stage_number):
            fase_naam = (project.stages[rs.stage_number - 1].name
                         if 0 <= rs.stage_number - 1 < len(project.stages)
                         else str(rs.stage_number))
            rijen.append([
                fase_naam,
                fmt_number(rs.max_moment_knm),
                fmt_number(rs.max_shear_kn),
                fmt_number(rs.max_disp_mm),
                fmt_number(rs.mob_moment_pct),
                fmt_number(rs.mob_grond_pct),
            ])
        sec.tables.append(ReportTable(
            id='conclusietabel_tabel',
            title='',
            columns=kolommen,
            rows=rijen,
        ))
        return sec

    # ------------------------------------------------------------------
    # Sectie 5: Resultatengrafieken
    # ------------------------------------------------------------------

    def _governing_stage_index(self, project: Project) -> int:
        """Geef de 0-gebaseerde index van de fase met het hoogste absoluut moment."""
        if not project.result_summaries:
            return max(0, len(project.stages) - 1)
        best = max(project.result_summaries, key=lambda r: r.max_moment_knm)
        return best.stage_number - 1

    def _bouw_grafiek_secties(
        self,
        project: Project,
        governing_step_key: str | None,
        disp_step_key: str | None,
    ) -> list[ReportSection]:
        """Bouw twee grafiek-secties: moment/dwarskracht (ULS) en vervorming (6.5)."""
        gov_idx = self._governing_stage_index(project)
        sec_mv = ReportSection(id='grafieken_moment_dwarskracht',
                               title='Momenten en dwarskrachten')
        sec_mv.images.append(ReportImageRequest(
            id='grafiek_moment_shear',
            caption='Momenten en dwarskrachten — maatgevende fase',
            figure_key='moment_shear',
            stage_index=gov_idx,
            step_key=governing_step_key,
        ))
        sec_disp = ReportSection(id='grafieken_vervorming', title='Vervormingen')
        sec_disp.images.append(ReportImageRequest(
            id='grafiek_displacement',
            caption='Vervormingen — stap 6.5',
            figure_key='displacement',
            stage_index=gov_idx,
            step_key=disp_step_key,
        ))
        return [sec_mv, sec_disp]

    # ------------------------------------------------------------------
    # Hoofd-methode
    # ------------------------------------------------------------------

    def build(
        self,
        project: Project,
        governing_step_key: str | None,
        disp_step_key: str | None,
    ) -> list[ReportSection]:
        """Bouw alle vijf secties van het damwand-hoofdstuk.

        Parameters
        ----------
        project:
            Actief project.
        governing_step_key:
            Sleutel van de maatgevende resultaatstap (ULS) voor moment/dwarskracht.
        disp_step_key:
            Sleutel van de resultaatstap voor vervorming (bevat '6.5').

        Returns
        -------
        list[ReportSection]
            Secties in volgorde: grondlagen, damwand, fases, conclusie, grafieken.
        """
        secties: list[ReportSection] = []
        secties += SoilTableBuilder().build(project)             # 1. Grondlagen
        secties.append(self._bouw_damwand_sectie(project))       # 2. Damwandgegevens
        secties += self._bouw_fase_secties(project)              # 3. Invoer per fase
        secties.append(self._bouw_conclusietabel(project))       # 4. Conclusietabel
        secties += self._bouw_grafiek_secties(                   # 5. Grafieken
            project, governing_step_key, disp_step_key
        )
        return secties
```

- [ ] **Stap 4: Tests laten slagen**

```bash
pytest tests/test_damwand_hoofdstuk_builder.py -v
```
Verwacht: alle tests PASS

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/damwand_hoofdstuk_builder.py tests/test_damwand_hoofdstuk_builder.py
git commit -m "feat: voltooi DamwandHoofdstukBuilder met conclusietabel, grafieken en build()"
```

---

## Task 4: Template aanmaken (damwand_stijlen.docx)

**Files:**
- Create: `templates/damwand_stijlen.docx` (via Python-script)

- [ ] **Stap 1: Maak de templates-map en het stijlenbestand aan**

Voer uit vanuit de projectmap:
```bash
python - <<'EOF'
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

os.makedirs('templates', exist_ok=True)
doc = Document()

# Paginamarges A4
section = doc.sections[0]
section.page_width  = Cm(21)
section.page_height = Cm(29.7)
section.left_margin   = Cm(2.5)
section.right_margin  = Cm(2.5)
section.top_margin    = Cm(2.5)
section.bottom_margin = Cm(2.0)

# Standaard lettertype
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(10)

# Heading 1
h1 = doc.styles['Heading 1']
h1.font.name = 'Calibri'
h1.font.size = Pt(14)
h1.font.bold = True
h1.font.color.rgb = RGBColor(0x24, 0x5B, 0x7A)  # DKIB blauw

# Heading 2
h2 = doc.styles['Heading 2']
h2.font.name = 'Calibri'
h2.font.size = Pt(11)
h2.font.bold = True
h2.font.color.rgb = RGBColor(0x24, 0x5B, 0x7A)

# Tabelstijl
try:
    tbl_style = doc.styles['Table Grid']
    tbl_style.font.name = 'Calibri'
    tbl_style.font.size = Pt(9)
except KeyError:
    pass  # stijl bestaat al in standaard Normal.dotx

doc.save('templates/damwand_stijlen.docx')
print('Template aangemaakt: templates/damwand_stijlen.docx')
EOF
```
Verwacht output: `Template aangemaakt: templates/damwand_stijlen.docx`

- [ ] **Stap 2: Verifieer dat het bestand bestaat**

```bash
python -c "from docx import Document; doc = Document('templates/damwand_stijlen.docx'); print('OK, stijlen:', [s.name for s in doc.styles if 'Heading' in s.name])"
```
Verwacht: `OK, stijlen: ['Heading 1', 'Heading 2', ...]`

- [ ] **Stap 3: Commit**

```bash
git add templates/damwand_stijlen.docx
git commit -m "feat: voeg Word stijlentemplate toe voor damwand-export"
```

---

## Task 5: WordHoofdstukExporter — secties schrijven

**Files:**
- Create: `exporters/word_hoofdstuk_exporter.py`
- Create: `tests/test_word_hoofdstuk_exporter.py`

- [ ] **Stap 1: Schrijf de falende tests**

`tests/test_word_hoofdstuk_exporter.py`:
```python
"""Tests voor WordHoofdstukExporter."""
from __future__ import annotations
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from docx import Document
from reporting.models import ReportSection, ReportField, ReportTable, ReportImageRequest, ReportMetadata
from exporters.word_hoofdstuk_exporter import WordHoofdstukExporter


TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'templates', 'damwand_stijlen.docx')


def _export(secties, metadata=None) -> Document:
    """Exporteer naar een tijdelijk bestand en lees terug."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        pad = f.name
    exp = WordHoofdstukExporter()
    fout = exp.export(
        sections=secties,
        metadata=metadata or ReportMetadata(project_name='Testproject'),
        project=None,
        template_path=TEMPLATE,
        output_path=pad,
    )
    assert fout is None, f'Export fout: {fout}'
    doc = Document(pad)
    os.unlink(pad)
    return doc


def test_export_maakt_bestand_aan() -> None:
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        pad = f.name
    exp = WordHoofdstukExporter()
    fout = exp.export(
        sections=[],
        metadata=ReportMetadata(project_name='P'),
        project=None,
        template_path=TEMPLATE,
        output_path=pad,
    )
    assert fout is None
    assert os.path.exists(pad)
    os.unlink(pad)


def test_sectietitel_wordt_heading() -> None:
    sec = ReportSection(id='test', title='Mijn Sectie')
    doc = _export([sec])
    teksten = [p.text for p in doc.paragraphs]
    assert 'Mijn Sectie' in teksten


def test_veld_wordt_paragraaf() -> None:
    sec = ReportSection(id='test', title='Sectie')
    sec.fields.append(ReportField('k', 'Profiel', 'AZ 14-700', ''))
    doc = _export([sec])
    tekst = ' '.join(p.text for p in doc.paragraphs)
    assert 'Profiel' in tekst
    assert 'AZ 14-700' in tekst


def test_tabel_kolommen_aanwezig() -> None:
    sec = ReportSection(id='test', title='Sectie')
    sec.tables.append(ReportTable(
        id='t', title='',
        columns=['Fase', 'Moment'],
        rows=[['F1', '100']],
    ))
    doc = _export([sec])
    assert len(doc.tables) >= 1
    header_cellen = [c.text for c in doc.tables[0].rows[0].cells]
    assert 'Fase' in header_cellen
    assert 'Moment' in header_cellen


def test_export_zonder_template_gebruikt_lege_doc() -> None:
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        pad = f.name
    fout = WordHoofdstukExporter().export(
        sections=[ReportSection(id='x', title='Y')],
        metadata=ReportMetadata(),
        project=None,
        template_path=None,
        output_path=pad,
    )
    assert fout is None
    os.unlink(pad)
```

- [ ] **Stap 2: Laat de tests falen**

```bash
pytest tests/test_word_hoofdstuk_exporter.py -v
```
Verwacht: `ImportError: No module named 'exporters.word_hoofdstuk_exporter'`

- [ ] **Stap 3: Implementeer de exporter (secties schrijven, nog geen figuren)**

`exporters/word_hoofdstuk_exporter.py`:
```python
"""WordHoofdstukExporter — exporteert het damwand-hoofdstuk naar Word."""
from __future__ import annotations
from pathlib import Path

from docx import Document
from docx.shared import Cm

from reporting.models import ReportSection, ReportMetadata


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
        """Render figuur naar PNG-bytes (headless). Overschreven in Task 6."""
        return None
```

- [ ] **Stap 4: Tests laten slagen**

```bash
pytest tests/test_word_hoofdstuk_exporter.py -v
```
Verwacht: alle tests PASS

- [ ] **Stap 5: Commit**

```bash
git add exporters/word_hoofdstuk_exporter.py tests/test_word_hoofdstuk_exporter.py
git commit -m "feat: voeg WordHoofdstukExporter toe met secties/tabellen schrijven"
```

---

## Task 6: WordHoofdstukExporter — figuurrendering

**Files:**
- Modify: `exporters/word_hoofdstuk_exporter.py`
- Modify: `tests/test_word_hoofdstuk_exporter.py`

- [ ] **Stap 1: Schrijf de falende tests**

Voeg toe aan `tests/test_word_hoofdstuk_exporter.py`:
```python
from unittest.mock import patch, MagicMock
from parsers.models import Project, FileBundle, SheetPilingElement, Stage, Surface


def _mini_project() -> Project:
    return Project(
        base_name='t', project_name='T', file_bundle=FileBundle(),
        sheet_piling=[SheetPilingElement(
            name='AZ 14-700', x=0.0, bottom=-10.0, top=-2.0, width=1.4,
        )],
        stages=[Stage(name='F1')],
        surfaces=[Surface(nr=1, name='MV', points=[{'x': -10, 'y': 0}, {'x': 10, 'y': 0}])],
    )


def test_figuur_placeholder_zonder_project() -> None:
    sec = ReportSection(id='test', title='Grafieken')
    sec.images.append(ReportImageRequest(
        id='fig1', caption='Dwarsdoorsnede fase 1',
        figure_key='section', stage_index=0, step_key=None,
    ))
    doc = _export([sec], metadata=ReportMetadata())
    tekst = ' '.join(p.text for p in doc.paragraphs)
    assert 'Figuur' in tekst  # placeholder tekst


def test_render_figuur_section_geeft_bytes() -> None:
    """render_figuur voor figure_key='section' geeft PNG-bytes terug."""
    from reporting.models import ReportImageRequest as RIR
    from exporters.word_hoofdstuk_exporter import WordHoofdstukExporter
    project = _mini_project()
    img_req = RIR(id='f', caption='c', figure_key='section', stage_index=0, step_key=None)
    exp = WordHoofdstukExporter()
    result = exp._render_figuur(img_req, project)
    assert result is not None
    assert result[:4] == b'\x89PNG'  # PNG magic bytes


def test_render_figuur_moment_shear_geeft_bytes() -> None:
    from reporting.models import ReportImageRequest as RIR
    from exporters.word_hoofdstuk_exporter import WordHoofdstukExporter
    project = _mini_project()
    img_req = RIR(id='f', caption='c', figure_key='moment_shear', stage_index=0, step_key=None)
    exp = WordHoofdstukExporter()
    result = exp._render_figuur(img_req, project)
    assert result is not None
    assert result[:4] == b'\x89PNG'
```

- [ ] **Stap 2: Laat de tests falen**

```bash
pytest tests/test_word_hoofdstuk_exporter.py::test_render_figuur_section_geeft_bytes -v
```
Verwacht: `AssertionError` (returns None)

- [ ] **Stap 3: Implementeer `_render_figuur` volledig**

Vervang de `_render_figuur` methode in `exporters/word_hoofdstuk_exporter.py`:
```python
    def _render_figuur(self, img_req, project) -> bytes | None:
        """Render figuur naar PNG-bytes met headless matplotlib.

        Ondersteunde figure_key waarden:
        - 'section'      : dwarsdoorsnede via SectionRenderer
        - 'moment_shear' : moment + dwarskracht via OutputRenderer
        - 'displacement' : vervorming via OutputRenderer
        """
        import io
        import matplotlib
        matplotlib.use('Agg')
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from app.settings import RenderSettings, ViewportSettings
        from renderers.section_renderer import SectionRenderer, y_range_for_project, x_range_for_project

        key = img_req.figure_key
        stage_index = img_req.stage_index or 0
        stage = (project.stages[stage_index]
                 if project.stages and 0 <= stage_index < len(project.stages)
                 else None)
        render_settings = RenderSettings()
        viewport_settings = ViewportSettings()

        try:
            if key == 'section':
                fig = Figure(figsize=(16 / 2.54, 12 / 2.54))
                FigureCanvasAgg(fig)
                ax = fig.add_subplot(111)
                y_min, y_max = y_range_for_project(project)
                x_min, x_max = x_range_for_project(project)
                viewport_settings.y_min = y_min - 1.0
                viewport_settings.y_max = y_max + 0.5
                viewport_settings.x_min = x_min
                viewport_settings.x_max = x_max
                SectionRenderer().render(ax, project, stage, render_settings, viewport_settings)
                fig.tight_layout()

            elif key in ('moment_shear', 'displacement'):
                from renderers.output_renderer import OutputRenderer, draw_result_chart
                from renderers.section_renderer import y_range_for_project as _yrange
                y_min, y_max = _yrange(project)
                step_key = img_req.step_key
                stage_number = stage_index + 1

                if key == 'moment_shear':
                    fig = Figure(figsize=(16 / 2.54, 10 / 2.54))
                    FigureCanvasAgg(fig)
                    axes = fig.subplots(1, 2, sharey=True)
                    charts = [('Momenten', 'kNm', 'moment'), ('Dwarskrachten', 'kN', 'shear')]
                    result_stage = (
                        project.result_steps[step_key].stages.get(stage_number)
                        if step_key and step_key in project.result_steps else None
                    )
                    for ax, (title, unit, series) in zip(axes, charts):
                        draw_result_chart(ax, title, unit, series, result_stage,
                                          project, stage, y_min, y_max, render_settings)
                else:  # displacement
                    fig = Figure(figsize=(8 / 2.54, 10 / 2.54))
                    FigureCanvasAgg(fig)
                    ax = fig.add_subplot(111)
                    result_stage = (
                        project.result_steps[step_key].stages.get(stage_number)
                        if step_key and step_key in project.result_steps else None
                    )
                    draw_result_chart(ax, 'Vervormingen', 'mm', 'disp', result_stage,
                                      project, stage, y_min, y_max, render_settings)
                fig.tight_layout()
            else:
                return None

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf.read()

        except Exception:
            return None
```

- [ ] **Stap 4: Tests laten slagen**

```bash
pytest tests/test_word_hoofdstuk_exporter.py -v
```
Verwacht: alle tests PASS

- [ ] **Stap 5: Commit**

```bash
git add exporters/word_hoofdstuk_exporter.py tests/test_word_hoofdstuk_exporter.py
git commit -m "feat: voeg headless figuurrendering toe aan WordHoofdstukExporter"
```

---

## Task 7: Export-knop in main_window.py

**Files:**
- Modify: `app/main_window.py`

- [ ] **Stap 1: Voeg de knop toe aan `_build_project_corner()`**

Zoek in `app/main_window.py` de methode `_build_project_corner()`. Vervang:
```python
    def _build_project_corner(self) -> QWidget:
        """Project-selector als corner-widget in de tab-balk."""
        corner = QWidget()
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)
        lbl = QLabel('Project:')
        lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #2c3e50;')
        layout.addWidget(lbl)
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(160)
        layout.addWidget(self._project_combo)
        return corner
```
Met:
```python
    def _build_project_corner(self) -> QWidget:
        """Project-selector + export-knop als corner-widget in de tab-balk."""
        corner = QWidget()
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)
        lbl = QLabel('Project:')
        lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #2c3e50;')
        layout.addWidget(lbl)
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(160)
        layout.addWidget(self._project_combo)
        self._btn_export_rapport = QPushButton('Exporteer rapport (Word)')
        self._btn_export_rapport.setStyleSheet(_BTN_PRIMARY)
        self._btn_export_rapport.setEnabled(False)
        layout.addWidget(self._btn_export_rapport)
        return corner
```

- [ ] **Stap 2: Verbind het signaal in `_connect_signals()`**

Voeg toe aan `_connect_signals()` in `app/main_window.py`, na de bestaande verbindingen:
```python
        self._btn_export_rapport.clicked.connect(self._on_export_hoofdstuk)
```

- [ ] **Stap 3: Activeer/deactiveer de knop in `_update_all()`**

Zoek de methode `_update_all()` in `app/main_window.py`. Voeg **bovenaan** de methode toe (na de openingsbrace):
```python
        heeft_project = bool(self._state.projects)
        self._btn_export_rapport.setEnabled(heeft_project)
```

- [ ] **Stap 4: Implementeer de handler `_on_export_hoofdstuk()`**

Voeg de volgende methode toe aan `MainWindow`, gegroepeerd bij de andere export-handlers:
```python
    def _on_export_hoofdstuk(self) -> None:
        """Exporteer het actieve project als Word-rapport."""
        from pathlib import Path
        from reporting.builders.damwand_hoofdstuk_builder import DamwandHoofdstukBuilder
        from exporters.word_hoofdstuk_exporter import WordHoofdstukExporter

        project = self._controller.active_project()
        if not project:
            QMessageBox.warning(self, 'Exporteer rapport', 'Geen actief project geladen.')
            return

        # Bepaal stap-sleutels
        stap_sleutels = list(project.result_steps.keys())
        governing_step_key = stap_sleutels[0] if stap_sleutels else None
        disp_step_key = next(
            (k for k in stap_sleutels if '6.5' in k), None
        )
        if disp_step_key is None and stap_sleutels:
            QMessageBox.warning(
                self, 'Exporteer rapport',
                'Geen resultaatstap met "6.5" gevonden. '
                'Vervormingsgrafiek wordt weggelaten.',
            )

        # Bestandsdialoog
        pad, _ = QFileDialog.getSaveFileName(
            self, 'Sla rapport op', f'{project.base_name}_rapport.docx',
            'Word-document (*.docx)',
        )
        if not pad:
            return

        # Bouw secties
        builder = DamwandHoofdstukBuilder()
        secties = builder.build(project, governing_step_key, disp_step_key)

        # Exporteer
        from reporting.models import ReportMetadata
        metadata = self._report_controller.build_metadata()
        template_pad = self._state.app_settings.word_template_path or 'templates/damwand_stijlen.docx'
        fout = WordHoofdstukExporter().export(
            sections=secties,
            metadata=metadata,
            project=project,
            template_path=template_pad,
            output_path=pad,
        )
        if fout:
            QMessageBox.warning(self, 'Exporteer rapport', f'Export mislukt:\n{fout}')
        else:
            QMessageBox.information(self, 'Exporteer rapport', f'Rapport opgeslagen:\n{pad}')
```

- [ ] **Stap 5: Controleer of `AppController` een `active_project()` methode heeft**

```bash
grep -n "active_project" app/controller.py
```

Als de methode niet bestaat, voeg haar toe aan `app/controller.py`:
```python
    def active_project(self):
        """Geef het actieve project terug, of None als geen project geladen."""
        if not self._state.projects:
            return None
        combo_index = getattr(self, '_active_index', 0)
        naam = list(self._state.projects.keys())
        return self._state.projects.get(naam[combo_index]) if naam else None
```

Als de methode al anders geïmplementeerd is, gebruik die bestaande versie.

- [ ] **Stap 6: Controleer of `ReportController` een `build_metadata()` methode heeft**

```bash
grep -n "build_metadata" app/report_controller.py
```

Als de methode niet bestaat, voeg haar toe aan `ReportController`:
```python
    def build_metadata(self) -> 'ReportMetadata':
        """Geef ReportMetadata op basis van de huidige rapport-state."""
        from reporting.models import ReportMetadata
        rs = self._report_state
        return ReportMetadata(
            project_name=getattr(rs, 'project_name', '') or '',
            client=getattr(rs, 'client', '') or '',
            author=getattr(rs, 'author', '') or '',
            date=getattr(rs, 'date', '') or '',
            revision=getattr(rs, 'revision', '') or '',
        )
```

- [ ] **Stap 7: Start de applicatie en test handmatig**

```bash
python run.pyw
```

Controleer:
1. Knop "Exporteer rapport (Word)" zichtbaar maar uitgeschakeld bij opstart
2. Na laden van een project wordt de knop actief
3. Klikken opent een opslagdialoog
4. Opgeslagen `.docx` bevat de vijf secties

- [ ] **Stap 8: Commit**

```bash
git add app/main_window.py app/controller.py app/report_controller.py
git commit -m "feat: voeg Export rapport knop toe aan hoofdvenster"
```

---

## Zelf-review

**Spec-dekking:**
- ✓ Sectie 1 Grondlagen → Task 3 (`SoilTableBuilder().build()`)
- ✓ Sectie 2 Damwandgegevens → Task 1 (`_bouw_damwand_sectie`)
- ✓ Sectie 3 Invoer per fase + figuren → Task 2 (`_bouw_fase_secties` + `ReportImageRequest(figure_key='section')`)
- ✓ Sectie 4 Conclusietabel → Task 3 (`_bouw_conclusietabel`)
- ✓ Sectie 5 Grafieken (moment/shear ULS + disp 6.5) → Task 3 (`_bouw_grafiek_secties`)
- ✓ Stijlentemplate → Task 4
- ✓ Word export met template → Task 5 + Task 6
- ✓ Main export knop + handler → Task 7
- ✓ Knop inactief zonder project → Task 7 stap 3
- ✓ Waarschuwing bij ontbrekende 6.5-stap → Task 7 stap 4

**Type consistentie:**
- `DamwandHoofdstukBuilder.build()` → `list[ReportSection]` ✓
- `WordHoofdstukExporter.export()` → `str | None` ✓
- `_render_figuur()` → `bytes | None` ✓
- `ReportImageRequest.figure_key` gebruikt in Tasks 2, 3 en 6 ✓

**Geen placeholders:** Alle methoden bevatten volledige implementaties. ✓
