# Grondsoortentabel als exporteerbaar selectie-item — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elk grondprofiel verschijnt als selecteerbaar item in de Selectie-tab en wordt meegenomen in de Excel-, Word- en HTML-preview-export.

**Architecture:** Een nieuwe `SoilTableBuilder` produceert één `ReportSection` per profiel. `ReportPackage` krijgt een generiek `extra_sections`-veld voor alle toekomstige niet-invoer/resultaat-secties. `ReportController` vult het plan en het pakket. Alle drie exporters (HTML, Excel, Word) worden uitgebreid om `extra_sections` te verwerken.

**Tech Stack:** Python 3.10+, PyQt6, openpyxl, python-docx. Tests met pytest.

---

## Bestandsoverzicht

| Actie   | Bestand                                              | Verantwoordelijkheid                        |
|---------|------------------------------------------------------|---------------------------------------------|
| Create  | `reporting/builders/soil_table_builder.py`           | Builder: profiel → ReportSection            |
| Create  | `tests/test_soil_table_builder.py`                   | Unit-tests voor SoilTableBuilder            |
| Modify  | `reporting/models.py`                                | `extra_sections` toevoegen aan ReportPackage|
| Modify  | `reporting/selection.py`                             | `build_package` accepteert extra_sections   |
| Modify  | `app/report_controller.py`                           | build_soil_sections, auto_populate, package |
| Modify  | `reporting/builders/html_preview_builder.py`         | Lookup via flat dict over alle 3 lijsten    |
| Modify  | `tests/test_html_preview_builder.py`                 | Test voor kind='grondsoorten'               |
| Modify  | `exporters/excel_exporter.py`                        | selected_ids + extra_sections               |
| Modify  | `exporters/word_exporter.py`                         | selected_ids + extra_sections               |

---

## Task 1: SoilTableBuilder

**Files:**
- Create: `reporting/builders/soil_table_builder.py`
- Create: `tests/test_soil_table_builder.py`

- [ ] **Stap 1: Schrijf de falende tests**

Maak `tests/test_soil_table_builder.py` aan:

```python
"""Tests voor SoilTableBuilder."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parsers.models import Project, FileBundle, Soil, SoilProfile, SoilLayer
from reporting.builders.soil_table_builder import SoilTableBuilder


def _maak_project(profielen=None, soils=None) -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=soils or [],
        profiles=profielen or [],
    )


def _maak_profiel(naam: str, lagen: list[SoilLayer]) -> SoilProfile:
    return SoilProfile(
        name=naam, normalized_name=naam.lower(),
        occurrence=1, x=None, y=None, layers=lagen,
    )


def _laag(nr: int, level: float, material: str) -> SoilLayer:
    return SoilLayer(nr=nr, level=level, wosp_top=0.0, wosp_bottom=0.0, material=material)


def _soil(naam: str, gd=17.0, gn=19.0, c=2.0, phi=32.5, delta=16.0,
          kh1=10.0, kh2=20.0, kh3=30.0) -> Soil:
    return Soil(name=naam, color='rgb(0,0,0)', color_int=None,
                gamma_dry=gd, gamma_wet=gn, cohesion=c, phi=phi,
                delta=delta, kh1=kh1, kh2=kh2, kh3=kh3)


def test_één_sectie_per_profiel() -> None:
    project = _maak_project(
        profielen=[
            _maak_profiel('Links', [_laag(1, 0.0, 'Zand')]),
            _maak_profiel('Rechts', [_laag(1, 0.0, 'Klei')]),
        ],
    )
    secties = SoilTableBuilder().build(project)
    assert len(secties) == 2


def test_sectie_id_gesaniteerd() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('Links Zand', [_laag(1, 0.0, 'Zand')])]
    )
    secties = SoilTableBuilder().build(project)
    assert secties[0].id == 'soil_table_links_zand'


def test_sectie_titel_correct() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('Links', [_laag(1, 0.0, 'Zand')])]
    )
    secties = SoilTableBuilder().build(project)
    assert secties[0].title == 'Grondsoortentabel \u2014 Links'


def test_tabel_bevat_11_kolommen() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [_laag(1, 0.0, 'Zand')])]
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    assert len(tabel.columns) == 11


def test_rijen_gevuld_met_soil_params() -> None:
    soil = _soil('Zand', gd=17.0, phi=32.5, kh1=10.0)
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
        soils=[soil],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    rij = tabel.rows[0]
    # kolom 0=BK, 1=OK, 2=Laagnaam, 3=γd, 4=γn, 5=c', 6=φ', 7=δ, 8=kh1, 9=kh2, 10=kh3
    assert rij[2] == 'Zand'
    assert '17' in rij[3]   # gamma_dry=17,0
    assert '32' in rij[6]   # phi=32,5


def test_bk_en_ok_correct() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    # Eerste rij: BK=0.0, OK=niveau van laag 2 = -5.0
    assert '0' in tabel.rows[0][0]
    assert '-5' in tabel.rows[0][1]


def test_laatste_laag_ok_is_streepje() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [
            _laag(1, 0.0, 'Zand'),
            _laag(2, -5.0, 'Klei'),
        ])],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    assert tabel.rows[-1][1] == '-'


def test_ontbrekende_soil_geeft_streepjes() -> None:
    project = _maak_project(
        profielen=[_maak_profiel('L', [_laag(1, 0.0, 'Onbekend')])],
        soils=[],
    )
    tabel = SoilTableBuilder().build(project)[0].tables[0]
    rij = tabel.rows[0]
    assert rij[3] == '-'   # gamma_dry
    assert rij[6] == '-'   # phi


def test_lege_profielen_geeft_lege_lijst() -> None:
    project = _maak_project(profielen=[])
    assert SoilTableBuilder().build(project) == []
```

- [ ] **Stap 2: Verifieer dat de tests falen**

```
cd "C:\Users\Thijs\Dropbox\DKIB_geotechniek\04 Apps\Dsheet_dashboard"
pytest tests/test_soil_table_builder.py -v
```

Verwacht: `ImportError` of `ModuleNotFoundError` op `soil_table_builder`.

- [ ] **Stap 3: Implementeer de builder**

Maak `reporting/builders/soil_table_builder.py` aan:

```python
"""SoilTableBuilder — bouwt grondsoortentabellen als ReportSection per profiel."""

from __future__ import annotations

import re

from parsers.models import Project, Soil, SoilProfile
from reporting.models import ReportSection, ReportTable
from utils.formatting import fmt_number

_KOLOMMEN: list[str] = [
    'BK laag [m NAP]',
    'OK laag [m NAP]',
    'Laag',
    '\u03b3d [kN/m\u00b3]',
    '\u03b3n [kN/m\u00b3]',
    "c'kar [kN/m\u00b2]",
    "\u03c6'kar [\u00b0]",
    '\u03b4 [\u00b0]',
    'kh1',
    'kh2',
    'kh3',
]


class SoilTableBuilder:
    """Bouwt een ReportSection per grondprofiel met alle grondparameters."""

    def build(self, project: Project) -> list[ReportSection]:
        """Bouw één ReportSection per profiel.

        Parameters
        ----------
        project:
            Actief project met profielen en grondsoorten.

        Returns
        -------
        list[ReportSection]
            Één sectie per profiel, lege lijst als er geen profielen zijn.
        """
        soil_map: dict[str, Soil] = {s.name: s for s in project.soils}
        return [self._bouw_sectie(profiel, soil_map) for profiel in project.profiles]

    def _bouw_sectie(
        self, profiel: SoilProfile, soil_map: dict[str, Soil]
    ) -> ReportSection:
        sec_id = 'soil_table_' + re.sub(r'\s+', '_', profiel.name.lower())
        sec = ReportSection(id=sec_id, title=f'Grondsoortentabel \u2014 {profiel.name}')
        sec.tables.append(self._bouw_tabel(profiel, soil_map, sec_id))
        return sec

    def _bouw_tabel(
        self,
        profiel: SoilProfile,
        soil_map: dict[str, Soil],
        sec_id: str,
    ) -> ReportTable:
        n = len(profiel.layers)
        rijen: list[list[str]] = []
        for i, laag in enumerate(profiel.layers):
            ok = fmt_number(profiel.layers[i + 1].level) if i + 1 < n else '-'
            soil = soil_map.get(laag.material)
            if soil:
                params: list[str] = [
                    fmt_number(soil.gamma_dry),
                    fmt_number(soil.gamma_wet),
                    fmt_number(soil.cohesion),
                    fmt_number(soil.phi),
                    fmt_number(soil.delta),
                    str(int(soil.kh1)) if soil.kh1 else '-',
                    str(int(soil.kh2)) if soil.kh2 else '-',
                    str(int(soil.kh3)) if soil.kh3 else '-',
                ]
            else:
                params = ['-'] * 8
            rijen.append([fmt_number(laag.level), ok, laag.material] + params)
        return ReportTable(
            id=f'{sec_id}_tabel',
            title='',
            columns=_KOLOMMEN,
            rows=rijen,
        )
```

- [ ] **Stap 4: Verifieer dat alle tests slagen**

```
pytest tests/test_soil_table_builder.py -v
```

Verwacht: alle 9 tests PASS.

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/soil_table_builder.py tests/test_soil_table_builder.py
git commit -m "feat: voeg SoilTableBuilder toe met unit-tests"
```

---

## Task 2: ReportPackage.extra_sections + ReportPlan.build_package

**Files:**
- Modify: `reporting/models.py`
- Modify: `reporting/selection.py`
- Modify: `tests/test_soil_table_builder.py`

- [ ] **Stap 1: Schrijf een falende test voor build_package met extra_sections**

Voeg onderaan `tests/test_soil_table_builder.py` toe:

```python
from reporting.models import ReportSection, ReportPackage, ReportMetadata
from reporting.selection import ReportPlan


def test_build_package_bevat_extra_sections() -> None:
    sec = ReportSection(id='soil_table_links', title='Grondsoortentabel \u2014 Links')
    plan = ReportPlan()
    pkg = plan.build_package(
        metadata=ReportMetadata(),
        input_sections=[],
        result_sections=[],
        extra_sections=[sec],
    )
    assert len(pkg.extra_sections) == 1
    assert pkg.extra_sections[0].id == 'soil_table_links'
```

- [ ] **Stap 2: Verifieer dat de test faalt**

```
pytest tests/test_soil_table_builder.py::test_build_package_bevat_extra_sections -v
```

Verwacht: `TypeError` (onbekend argument `extra_sections`).

- [ ] **Stap 3: Voeg `extra_sections` toe aan `ReportPackage`**

In `reporting/models.py`, voeg het veld toe aan de `ReportPackage` dataclass, na `selected_items`:

```python
    extra_sections: list[ReportSection] = field(default_factory=list)
```

De volledige `ReportPackage` ziet er dan zo uit:

```python
@dataclass
class ReportPackage:
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    input_sections: list[ReportSection] = field(default_factory=list)
    result_sections: list[ReportSection] = field(default_factory=list)
    selected_items: list[ReportItem] = field(default_factory=list)
    extra_sections: list[ReportSection] = field(default_factory=list)
    template_excel: str | None = None
    template_word: str | None = None
```

- [ ] **Stap 4: Breid `ReportPlan.build_package` uit**

In `reporting/selection.py`, vervang de `build_package`-methode:

```python
    def build_package(
        self,
        metadata: ReportMetadata,
        input_sections: list[ReportSection],
        result_sections: list[ReportSection],
        extra_sections: list[ReportSection] | None = None,
    ) -> ReportPackage:
        """Bouw een ReportPackage op basis van huidige plan en secties."""
        return ReportPackage(
            metadata=metadata,
            input_sections=input_sections,
            result_sections=result_sections,
            selected_items=list(self.items),
            extra_sections=extra_sections or [],
        )
```

- [ ] **Stap 5: Verifieer dat alle tests slagen**

```
pytest tests/test_soil_table_builder.py -v
```

Verwacht: alle 10 tests PASS.

- [ ] **Stap 6: Commit**

```bash
git add reporting/models.py reporting/selection.py tests/test_soil_table_builder.py
git commit -m "feat: voeg extra_sections toe aan ReportPackage en ReportPlan.build_package"
```

---

## Task 3: ReportController

**Files:**
- Modify: `app/report_controller.py`

- [ ] **Stap 1: Importeer SoilTableBuilder bovenaan het bestand**

In `app/report_controller.py`, voeg toe na de bestaande builder-imports:

```python
from reporting.builders.soil_table_builder import SoilTableBuilder
```

- [ ] **Stap 2: Voeg `build_soil_sections` toe als methode**

Voeg de methode toe in de `# Builders`-sectie, na `build_result_descriptions`:

```python
    def build_soil_sections(self) -> list[ReportSection]:
        """Bouw grondsoortentabelsecties voor het actieve project.

        Returns
        -------
        list[ReportSection]
            Één sectie per grondprofiel, lege lijst als er geen project is.
        """
        project = self._app.get_active_project()
        if not project:
            return []
        return SoilTableBuilder().build(project)
```

- [ ] **Stap 3: Breid `auto_populate_plan` uit**

In `auto_populate_plan`, voeg de grondsoorten-loop toe na de resultaat-loop. De volledige methode wordt:

```python
    def auto_populate_plan(self) -> None:
        """Vul het rapportplan automatisch met items vanuit de builders.

        Voegt alleen items toe die er nog niet in zitten (op id).
        """
        from reporting.models import ReportItem
        input_secs = self.build_input_descriptions()
        result_secs = self.build_result_descriptions()
        for sec in input_secs:
            self._report.plan.add_item(ReportItem(
                id=f'input_{sec.id}',
                kind='invoer',
                caption=sec.title,
                source_ref=sec.id,
            ))
        for sec in result_secs:
            self._report.plan.add_item(ReportItem(
                id=f'result_{sec.id}',
                kind='resultaat',
                caption=sec.title,
                source_ref=sec.id,
            ))
        for sec in self.build_soil_sections():
            self._report.plan.add_item(ReportItem(
                id=f'grondsoorten_{sec.id}',
                kind='grondsoorten',
                caption=sec.title,
                source_ref=sec.id,
            ))
```

- [ ] **Stap 4: Breid `build_package` uit**

Vervang de `build_package`-methode:

```python
    def build_package(self) -> ReportPackage:
        """Bouw een ReportPackage op basis van huidige state."""
        input_secs = self.build_input_descriptions()
        result_secs = self.build_result_descriptions()
        soil_secs = self.build_soil_sections()
        pkg = self._report.plan.build_package(
            self._report.metadata, input_secs, result_secs,
            extra_sections=soil_secs,
        )
        pkg.template_excel = self._report.template_excel
        pkg.template_word = self._report.template_word
        return pkg
```

- [ ] **Stap 5: Draai alle bestaande tests om regressies te controleren**

```
pytest tests/ -v
```

Verwacht: alle bestaande tests PASS, geen nieuwe failures.

- [ ] **Stap 6: Commit**

```bash
git add app/report_controller.py
git commit -m "feat: voeg grondsoorten toe aan auto_populate_plan en build_package"
```

---

## Task 4: HtmlPreviewBuilder

**Files:**
- Modify: `reporting/builders/html_preview_builder.py`
- Modify: `tests/test_html_preview_builder.py`

- [ ] **Stap 1: Schrijf een falende test**

Voeg toe aan `tests/test_html_preview_builder.py`:

```python
def test_grondsoorten_sectie_opgenomen_bij_kind_grondsoorten() -> None:
    """kind='grondsoorten' → sectie uit extra_sections zichtbaar in HTML."""
    from reporting.models import ReportTable
    sec = ReportSection(id='soil_table_links', title='Grondsoortentabel \u2014 Links')
    tbl = ReportTable(
        id='t', title='',
        columns=['BK [m NAP]', 'Laag'],
        rows=[['-5,0', 'Zand']],
    )
    sec.tables.append(tbl)
    item = ReportItem(
        id='grondsoorten_soil_table_links',
        kind='grondsoorten',
        caption='Grondsoortentabel \u2014 Links',
        source_ref='soil_table_links',
    )
    pkg = ReportPackage(extra_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Grondsoortentabel' in html
    assert 'Zand' in html
```

- [ ] **Stap 2: Verifieer dat de test faalt**

```
pytest tests/test_html_preview_builder.py::test_grondsoorten_sectie_opgenomen_bij_kind_grondsoorten -v
```

Verwacht: FAIL — `'Grondsoortentabel' not in html`.

- [ ] **Stap 3: Pas de `build`-methode aan**

In `reporting/builders/html_preview_builder.py`, vervang de `build`-methode volledig:

```python
    def build(self, package: ReportPackage) -> str:
        """Genereer HTML-string voor de geselecteerde secties.

        Parameters
        ----------
        package:
            Rapportpakket met invoer-, resultaat- en extra-secties en de selectielijst.

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
            sec = alle_secties.get(item.source_ref)
            if sec is not None:
                secties.append(self._sectie_html(sec))

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
```

- [ ] **Stap 4: Verifieer dat alle tests slagen**

```
pytest tests/test_html_preview_builder.py -v
```

Verwacht: alle tests PASS (inclusief de nieuwe).

- [ ] **Stap 5: Commit**

```bash
git add reporting/builders/html_preview_builder.py tests/test_html_preview_builder.py
git commit -m "feat: HtmlPreviewBuilder ondersteunt extra_sections via flat sectie-lookup"
```

---

## Task 5: ExcelExporter en WordExporter

**Files:**
- Modify: `exporters/excel_exporter.py`
- Modify: `exporters/word_exporter.py`

- [ ] **Stap 1: Pas `ExcelExporter.export` aan**

In `exporters/excel_exporter.py`, vervang in de `export`-methode het blok met `selected_ids` en de sectieloop (beide in het `else`-blok na `self._write_metadata`):

**Oud:**
```python
                all_sections = package.input_sections + package.result_sections
                selected_ids = {f'input_{i.source_ref}' for i in package.selected_items
                                if i.kind == 'invoer'} | \
                               {f'result_{i.source_ref}' for i in package.selected_items
                                if i.kind == 'resultaat'}
                for sec in all_sections:
                    # Als er geselecteerde items zijn, filter dan; anders schrijf alles
                    item_id_input = f'input_{sec.id}'
                    item_id_result = f'result_{sec.id}'
                    if selected_ids and item_id_input not in selected_ids \
                            and item_id_result not in selected_ids:
                        continue
                    self._write_section(wb, sec)
```

**Nieuw:**
```python
                selected_ids = {
                    i.source_ref for i in package.selected_items if i.source_ref
                }
                all_sections = (
                    package.input_sections
                    + package.result_sections
                    + package.extra_sections
                )
                for sec in all_sections:
                    if selected_ids and sec.id not in selected_ids:
                        continue
                    self._write_section(wb, sec)
```

- [ ] **Stap 2: Pas ook het mapping-pad aan in `_write_with_mapping`**

In de methode `_write_with_mapping` in `exporters/excel_exporter.py`, vervang:

```python
        all_sections = package.input_sections + package.result_sections
```

door:

```python
        all_sections = (
            package.input_sections
            + package.result_sections
            + package.extra_sections
        )
```

- [ ] **Stap 3: Pas `WordExporter.export` aan**

In `exporters/word_exporter.py`, vervang in de `export`-methode het blok met `selected_ids` en de sectieloop (beide in het `else`-blok na `self._write_metadata`):

**Oud:**
```python
                all_sections = package.input_sections + package.result_sections
                selected_ids = {f'input_{i.source_ref}' for i in package.selected_items
                                if i.kind == 'invoer'} | \
                               {f'result_{i.source_ref}' for i in package.selected_items
                                if i.kind == 'resultaat'}
                for sec in all_sections:
                    item_id_input = f'input_{sec.id}'
                    item_id_result = f'result_{sec.id}'
                    if selected_ids and item_id_input not in selected_ids \
                            and item_id_result not in selected_ids:
                        continue
                    self._write_section(doc, sec)
```

**Nieuw:**
```python
                selected_ids = {
                    i.source_ref for i in package.selected_items if i.source_ref
                }
                all_sections = (
                    package.input_sections
                    + package.result_sections
                    + package.extra_sections
                )
                for sec in all_sections:
                    if selected_ids and sec.id not in selected_ids:
                        continue
                    self._write_section(doc, sec)
```

- [ ] **Stap 4: Pas ook het mapping-pad aan in `_write_with_mapping`**

In de methode `_write_with_mapping` in `exporters/word_exporter.py`, vervang:

```python
        all_sections = package.input_sections + package.result_sections
```

door:

```python
        all_sections = (
            package.input_sections
            + package.result_sections
            + package.extra_sections
        )
```

- [ ] **Stap 5: Draai alle tests**

```
pytest tests/ -v
```

Verwacht: alle tests PASS.

- [ ] **Stap 6: Commit**

```bash
git add exporters/excel_exporter.py exporters/word_exporter.py
git commit -m "feat: exporters ondersteunen extra_sections met uniforme source_ref-filtering"
```

---

## Verificatie na implementatie

Start de app en laad een project met meerdere profielen:

```
python run.pyw
```

Controleer:
1. Na het verwerken van bestanden: Selectie-tab toont items `[grondsoorten] Grondsoortentabel — <profielnaam>` voor elk profiel
2. Items zijn herordend en verwijderbaar via de knoppen
3. Excel-export met een grondsoort-item geselecteerd → werkblad `Grondsoortentabel — <naam>` aanwezig met 11 kolommen en de juiste rijen
4. Word-export idem — sectiekop `Grondsoortentabel — <naam>` met tabel
