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
