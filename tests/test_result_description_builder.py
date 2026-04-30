"""Tests voor ResultDescriptionBuilder — labels en kolomgroepen."""

from __future__ import annotations

from reporting.builders.result_description_builder import (
    ResultDescriptionBuilder,
    is_bgt_step_key,
    is_ugt_step_key,
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


def _maak_project_met_extremen() -> Project:
    """Minimaal project waarin UGT en BGT bewust verschillende stappen zijn."""
    fases = [Stage(name='Start'), Stage(name='Eindsituatie')]

    stap_64 = ResultStep(raw_step='CUR 166 6.4')
    stap_64.stages[1] = ResultStage(
        stage_number=1,
        points=[
            ResultPoint(depth=0.0, moment=90.0, shear=35.0, disp=2.0),
            ResultPoint(depth=-5.0, moment=-120.0, shear=-40.0, disp=-3.0),
        ],
    )

    stap_65 = ResultStep(raw_step='CUR 166 6.5')
    stap_65.stages[2] = ResultStage(
        stage_number=2,
        points=[
            ResultPoint(depth=0.0, moment=999.0, shear=888.0, disp=6.0),
            ResultPoint(depth=-6.0, moment=-750.0, shear=-777.0, disp=-12.0),
        ],
    )

    stap_factor = ResultStep(raw_step='CUR 166 6.5 x factor')
    stap_factor.stages[2] = ResultStage(
        stage_number=2,
        points=[
            ResultPoint(depth=0.0, moment=140.0, shear=60.0, disp=1.0),
            ResultPoint(depth=-7.0, moment=-210.0, shear=-95.0, disp=-2.0),
        ],
    )

    return Project(
        base_name='extremen',
        project_name='Extremen',
        file_bundle=FileBundle(),
        stages=fases,
        result_steps={
            'CUR 166 6.4': stap_64,
            'CUR 166 6.5': stap_65,
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


def test_ugt_bgt_stapdefinitie() -> None:
    """6.5 is BGT; 6.1 t/m 6.4 plus 6.5 x factor zijn UGT."""
    assert is_ugt_step_key('CUR 166 6.4') is True
    assert is_ugt_step_key('CUR 166 6.5 x factor') is True
    assert is_ugt_step_key('CUR 166 6.5 × factor') is True
    assert is_ugt_step_key('CUR 166 6.5') is False
    assert is_bgt_step_key('CUR 166 6.5') is True
    assert is_bgt_step_key('CUR 166 6.5 x factor') is False


def test_find_extreme_negeert_bgt_voor_ugt_moment() -> None:
    """Msd gebruikt UGT-stappen, dus de grotere gewone 6.5-waarde telt niet."""
    builder = ResultDescriptionBuilder()
    project = _maak_project_met_extremen()

    waarde, fase, stap, diepte = builder._find_extreme(
        project, 'moment', is_ugt_step_key
    )

    assert waarde == -210.0
    assert fase == 2
    assert stap == 'CUR 166 6.5 x factor'
    assert diepte == -7.0


def test_extremen_overzicht_bouwt_3x3_figuurgroep() -> None:
    """Nieuwe sectie bevat drie headers, drie figuurverzoeken en drie bronregels."""
    builder = ResultDescriptionBuilder()
    project = _maak_project_met_extremen()

    sectie = builder._build_extremen_overzicht(project)
    groep = sectie.image_groups[0]

    assert sectie.id == 'extremen_overzicht'
    assert groep.headers[0].startswith('Msd = 210')
    assert groep.headers[1].startswith('Dsd = 95')
    assert groep.headers[2].startswith('Urep BGT = 12')
    assert groep.images[0].figure_key == 'moment_curve'
    assert groep.images[1].figure_key == 'shear_curve'
    assert groep.images[2].figure_key == 'disp_curve'
    assert groep.images[2].step_key == 'CUR 166 6.5'
