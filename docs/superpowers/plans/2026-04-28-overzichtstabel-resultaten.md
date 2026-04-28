# Overzichtstabel resultaten — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Toon een gegroepeerde samenvattingstabel (momenten / dwarskrachten / vervormingen per fase × CUR 166-stap) onderaan het tabblad "Resultaatbeschrijving".

**Architecture:** Twee bestanden. `result_description_builder.py` levert al de data via `_per_phase_summary()`; labels en eenheden worden gecorrigeerd. `tab_result_desc._maak_styled_tabel()` wordt uitgebreid met een optionele groepkop-rij (colspan via QGridLayout) die activeert wanneer `table.column_groups` gevuld is.

**Tech Stack:** Python 3.10+, PyQt6, pytest

---

## Bestandsoverzicht

| Bestand | Wijziging |
|---|---|
| `reporting/builders/result_description_builder.py` | `_step_short_label()` en `_per_phase_summary()` — labels en eenheden |
| `ui/tabs/tab_result_desc.py` | `_maak_styled_tabel()` — 2-rij koptabel met colspan |
| `tests/test_result_description_builder.py` | Nieuw testbestand |
| `tests/test_tab_result_desc.py` | Nieuw testbestand |

---

## Task 1: Labels en eenheden in `result_description_builder.py`

**Files:**
- Modify: `reporting/builders/result_description_builder.py:33-36` (`_step_short_label`)
- Modify: `reporting/builders/result_description_builder.py:134-169` (`_per_phase_summary`)
- Create: `tests/test_result_description_builder.py`

- [ ] **Stap 1: Schrijf de falende tests**

Maak `tests/test_result_description_builder.py` aan met deze inhoud:

```python
"""Tests voor ResultDescriptionBuilder — labels en kolomgroepen."""

from __future__ import annotations

from reporting.builders.result_description_builder import (
    ResultDescriptionBuilder,
    _step_short_label,
)
from parsers.models import (
    Project, Stage, FileBundle,
    ResultStep, ResultStage, ResultPoint,
)


def _maak_project() -> Project:
    """Minimaal project met één fase en twee verificatiestappen."""
    fase = Stage(name='Fase 1')
    punt = ResultPoint(depth=0.0, moment=100.0, shear=50.0, disp=0.01)

    stap_61 = ResultStep(raw_step='CUR 166 6.1')
    stap_61.stages[1] = ResultStage(stage_number=1, points=[punt])

    stap_factor = ResultStep(raw_step='CUR 166 6.5 x factor')
    stap_factor.stages[1] = ResultStage(stage_number=1, points=[punt])

    return Project(
        base_name='test',
        project_name='test',
        file_bundle=FileBundle(),
        stages=[fase],
        result_steps={
            'CUR 166 6.1': stap_61,
            'CUR 166 6.5 x factor': stap_factor,
        },
    )


def test_step_short_label_regulier() -> None:
    assert _step_short_label('CUR 166 6.1') == '6.1'


def test_step_short_label_factor_vol_woord() -> None:
    """Verwacht '6.5 × factor', niet '6.5 × f'."""
    assert _step_short_label('CUR 166 6.5 x factor') == '6.5 × factor'


def test_per_phase_summary_kolommen_geen_prefix() -> None:
    """Kolomlabels mogen geen 'M ', 'V ' of 'u ' prefix hebben."""
    builder = ResultDescriptionBuilder()
    project = _maak_project()
    secs = builder.build(project, 0, 'CUR 166 6.1')
    tabel = secs[1].tables[0]
    niet_fase = [k for k in tabel.columns if k != 'Fase']
    assert not any(k.startswith(('M ', 'V ', 'u ')) for k in niet_fase)


def test_per_phase_summary_column_groups_eenheden() -> None:
    """Groepstitels bevatten 'kNm' en 'kN' (zonder /m)."""
    builder = ResultDescriptionBuilder()
    project = _maak_project()
    secs = builder.build(project, 0, 'CUR 166 6.1')
    tabel = secs[1].tables[0]
    labels = [g[0] for g in tabel.column_groups]
    assert 'Momenten (kNm)' in labels
    assert 'Dwarskrachten (kN)' in labels
    assert 'Vervormingen (mm)' in labels


def test_per_phase_summary_kolommen_herhaald_per_groep() -> None:
    """Staplabels worden drie keer herhaald (één per groep), niet geprefixeerd."""
    builder = ResultDescriptionBuilder()
    project = _maak_project()
    secs = builder.build(project, 0, 'CUR 166 6.1')
    tabel = secs[1].tables[0]
    # 2 stappen → 'Fase' + 2×3 = 7 kolommen
    assert len(tabel.columns) == 7
    # Kolom 1 en 3 en 5 zijn alledrie '6.1' (herhaling per groep)
    assert tabel.columns[1] == tabel.columns[3] == tabel.columns[5] == '6.1'
```

- [ ] **Stap 2: Draai de tests en controleer dat ze falen**

```
pytest tests/test_result_description_builder.py -v
```

Verwacht: alle tests FAIL (functies geven nog oude waarden terug).

- [ ] **Stap 3: Pas `_step_short_label` aan**

In `reporting/builders/result_description_builder.py`, regel 36:

Vervang:
```python
        return m.group(1).replace(' x factor', ' × f')
```
Door:
```python
        return m.group(1).replace(' x factor', ' × factor')
```

- [ ] **Stap 4: Pas `_per_phase_summary` aan**

In `reporting/builders/result_description_builder.py`, vervang regels 134–169 (het blok vanaf `# Één brede tabel` t/m `return sec`):

```python
        # Één brede tabel: Fase | stap… (Momenten) | stap… (Dwarskrachten) | stap… (Vervormingen)
        kolommen = (
            ['Fase']
            + list(stap_labels)
            + list(stap_labels)
            + list(stap_labels)
        )
        sep_cols = [1 + n, 1 + 2 * n]  # begin Dwarskrachten- en Vervormingen-groep

        rows: list[list[str]] = []
        for stage_num in alle_stages:
            rij: list[str] = [self._stage_naam(project, stage_num)]
            for attr in ('moment', 'shear', 'disp'):
                for sk in stap_keys:
                    step = project.result_steps[sk]
                    rs = step.stages.get(stage_num)
                    ex = self._extremes(rs, attr) if rs else None
                    rij.append(
                        fmt_number(max(abs(ex[0]), abs(ex[2]))) if ex else '-'
                    )
            rows.append(rij)

        sec.tables.append(ReportTable(
            id='summary_resultaten',
            title='',
            columns=kolommen,
            rows=rows,
            separator_before_cols=sep_cols,
            column_groups=[
                ('', 1),
                ('Momenten (kNm)', n),
                ('Dwarskrachten (kN)', n),
                ('Vervormingen (mm)', n),
            ],
        ))
        return sec
```

- [ ] **Stap 5: Draai de tests en controleer dat ze slagen**

```
pytest tests/test_result_description_builder.py -v
```

Verwacht: alle 5 tests PASS.

- [ ] **Stap 6: Draai de volledige testsuite om regressies te checken**

```
pytest tests/ -v --ignore=tests/test_tab_result_desc.py
```

Verwacht: alle bestaande tests PASS.

- [ ] **Stap 7: Commit**

```bash
git add reporting/builders/result_description_builder.py tests/test_result_description_builder.py
git commit -m "feat: kolomlabels en eenheden overzichtstabel gecorrigeerd"
```

---

## Task 2: 2-rij koptabel in `tab_result_desc._maak_styled_tabel()`

**Files:**
- Modify: `ui/tabs/tab_result_desc.py:137-187` (`_maak_styled_tabel`)
- Create: `tests/test_tab_result_desc.py`

- [ ] **Stap 1: Schrijf de falende tests**

Maak `tests/test_tab_result_desc.py` aan:

```python
"""Tests voor TabResultDesc._maak_styled_tabel — groepkoppenrij."""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ui.tabs.tab_result_desc import TabResultDesc
from reporting.models import ReportTable


def _tabel_met_groepen() -> ReportTable:
    return ReportTable(
        id='test',
        title='',
        columns=['Fase', '6.1', '6.1'],
        rows=[['Fase 1', '100', '50'], ['Fase 2', '200', '80']],
        column_groups=[('', 1), ('Momenten (kNm)', 1), ('Dwarskrachten (kN)', 1)],
    )


def _tabel_zonder_groepen() -> ReportTable:
    return ReportTable(
        id='simpel',
        title='',
        columns=['Naam', 'Waarde'],
        rows=[['Ankerkracht', '45']],
    )


def test_zonder_groepen_geen_uitzondering(qapp) -> None:
    """Bestaand gedrag: tabel zonder column_groups geeft gewoon een widget terug."""
    tab = TabResultDesc()
    widget = tab._maak_styled_tabel(_tabel_zonder_groepen())
    assert widget is not None


def test_met_groepen_geen_uitzondering(qapp) -> None:
    """Tabel met column_groups mag niet crashen."""
    tab = TabResultDesc()
    widget = tab._maak_styled_tabel(_tabel_met_groepen())
    assert widget is not None


def test_groeplabels_zichtbaar_in_widget(qapp) -> None:
    """Groeplabels 'Momenten (kNm)' en 'Dwarskrachten (kN)' zijn aanwezig als QLabel."""
    tab = TabResultDesc()
    widget = tab._maak_styled_tabel(_tabel_met_groepen())
    labels = [w.text() for w in widget.findChildren(QLabel)]
    assert 'Momenten (kNm)' in labels
    assert 'Dwarskrachten (kN)' in labels


def test_datarijen_zichtbaar_in_widget(qapp) -> None:
    """Datawaarden uit de rijen zijn aanwezig als QLabel."""
    tab = TabResultDesc()
    widget = tab._maak_styled_tabel(_tabel_met_groepen())
    labels = [w.text() for w in widget.findChildren(QLabel)]
    assert 'Fase 1' in labels
    assert '100' in labels
    assert 'Fase 2' in labels
```

- [ ] **Stap 2: Draai de tests en controleer dat ze falen**

```
pytest tests/test_tab_result_desc.py -v
```

Verwacht: `test_met_groepen_geen_uitzondering`, `test_groeplabels_zichtbaar_in_widget` en `test_datarijen_zichtbaar_in_widget` FAIL (groepkoppen worden nog niet gegenereerd).

- [ ] **Stap 3: Vervang `_maak_styled_tabel` volledig**

In `ui/tabs/tab_result_desc.py`, vervang de complete methode `_maak_styled_tabel` (regels 137–187):

```python
    def _maak_styled_tabel(self, table) -> QWidget:
        """Rendert een ReportTable als gestijlde grid-tabel.

        Ondersteunt optioneel een groepkop-rij (rij 0) wanneer
        table.column_groups gevuld is; kolomkoppen komen dan op rij 1.
        """
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        buitenste = QHBoxLayout(wrapper)
        buitenste.setContentsMargins(0, 0, 0, 0)
        buitenste.setSpacing(0)

        frame = QFrame()
        frame.setStyleSheet(f'QFrame {{ background: white; border: 1px solid {_BORDER}; }}')
        frame.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        buitenste.addWidget(frame)
        buitenste.addStretch()

        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        n_cols = len(table.columns)
        heeft_groepen = bool(table.column_groups)
        kop_rij = 1 if heeft_groepen else 0
        data_start = kop_rij + 1

        # Groepkoppen (grid-rij 0) — alleen als column_groups gevuld is
        if heeft_groepen:
            col_offset = 0
            for groep_label, colspan in table.column_groups:
                lbl = QLabel(groep_label)
                lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                groep_bg = _HDR_BG if not groep_label else '#274f77'
                border_r = ('border-right: 1px solid #1d4568;'
                             if col_offset + colspan < n_cols else '')
                lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 10px; font-weight: 700; '
                    f'color: {_HDR_FG}; background: {groep_bg}; '
                    f'padding: 5px 10px; {border_r}'
                )
                grid.addWidget(lbl, 0, col_offset, 1, colspan)
                col_offset += colspan

        # Kolomkoppen (grid-rij kop_rij)
        for col, kop in enumerate(table.columns):
            lbl = QLabel(kop)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            border_r = 'border-right: 1px solid #1d4568;' if col < n_cols - 1 else ''
            lbl.setStyleSheet(
                f'font-family: {_FONT}; font-size: 10px; font-weight: 600; '
                f'color: #b8d4ea; background: {_HDR_BG}; '
                f'padding: 6px 10px; {border_r}'
            )
            grid.addWidget(lbl, kop_rij, col)

        # Datarijen (grid-rij data_start+)
        for row_i, rij in enumerate(table.rows):
            bg = _ROW_ODD_BG if row_i % 2 == 0 else _ROW_EVN_BG
            is_last = row_i == len(table.rows) - 1
            border_b = '' if is_last else f'border-bottom: 1px solid {_ROW_SEP};'
            for col, cel in enumerate(rij):
                uitlijning = (Qt.AlignmentFlag.AlignLeft if col == 0
                              else Qt.AlignmentFlag.AlignRight)
                cel_lbl = QLabel(cel)
                cel_lbl.setAlignment(uitlijning | Qt.AlignmentFlag.AlignVCenter)
                border_r = (f'border-right: 1px solid {_ROW_SEP};'
                             if col < n_cols - 1 else '')
                cel_lbl.setStyleSheet(
                    f'font-family: {_FONT}; font-size: 12px; color: {_VALUE_CLR}; '
                    f'background: {bg}; padding: 6px 10px; {border_r} {border_b}'
                )
                grid.addWidget(cel_lbl, data_start + row_i, col)

        return wrapper
```

- [ ] **Stap 4: Draai de tests en controleer dat ze slagen**

```
pytest tests/test_tab_result_desc.py -v
```

Verwacht: alle 4 tests PASS.

- [ ] **Stap 5: Draai de volledige testsuite**

```
pytest tests/ -v
```

Verwacht: alle tests PASS, geen regressies.

- [ ] **Stap 6: Commit**

```bash
git add ui/tabs/tab_result_desc.py tests/test_tab_result_desc.py
git commit -m "feat: gegroepeerde 2-rij koptabel in resultaattabel-renderer"
```

---

## Task 3: Visuele verificatie

- [ ] **Stap 1: Start de applicatie**

```
python run.pyw
```

- [ ] **Stap 2: Laad een project met .shd-bestand**

Open een project via de importknop. Klik "Verwerk".

- [ ] **Stap 3: Ga naar tabblad "Resultaatbeschrijving"**

Verwacht onderaan de tab:
- QGroupBox "Maximale resultaten per fase"
- Groepkop-rij: lege cel | **Momenten (kNm)** | **Dwarskrachten (kN)** | **Vervormingen (mm)**
- Kolomkop-rij: Fase | 6.1 | 6.2 | … | 6.5 × factor | 6.1 | … | 6.5 × factor | 6.1 | … | 6.5 × factor
- Datarijen: één per fase, met waarden of "-"

- [ ] **Stap 4: Controleer dat de ankerkrachtentabel boven de samenvattingstabel staat en correct gerenderd wordt**

De "Ankerkrachten en stempelkrachten" QGroupBox moet nog steeds werken zonder groepkoppen (vlakke koptabel). Controleer dat die er normaal uitziet.
