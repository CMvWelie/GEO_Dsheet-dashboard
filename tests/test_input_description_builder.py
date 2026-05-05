"""Tests voor InputDescriptionBuilder."""

from __future__ import annotations

from parsers.models import (
    FileBundle,
    HorizontalLineLoad,
    Moment,
    Project,
    Stage,
)
from reporting.builders.input_description_builder import InputDescriptionBuilder


def test_build_all_stages_gebruikt_value_voor_moment_en_lijnlast() -> None:
    """Moment- en lijnlastwaarden komen uit het domeinveld ``value``."""
    project = Project(
        base_name='p',
        project_name='P',
        file_bundle=FileBundle(),
        stages=[
            Stage(
                name='Fase 1',
                moments=['Leuningmoment'],
                horizontal_line_loads=['Leuninglast'],
            )
        ],
        moments=[
            Moment(
                nr=1,
                level=-1.0,
                value=12.5,
                permanent=1.0,
                favourable=0.0,
                name='Leuningmoment',
            )
        ],
        horizontal_line_loads=[
            HorizontalLineLoad(
                nr=1,
                level=-1.0,
                value=7.5,
                permanent=1.0,
                favourable=0.0,
                name='Leuninglast',
            )
        ],
    )

    cards = InputDescriptionBuilder().build_all_stages(project)
    waarden = {row.label: row.value for row in cards[0].rows}

    assert waarden['Leuningmoment'] == '12,5 [kNm/m]'
    assert waarden['Leuninglast'] == '7,5 [kN/m]'


def test_faserow_extra_lines_standaard_leeg() -> None:
    from reporting.builders.input_description_builder import FaseRow
    rij = FaseRow(label='Test', value='0,0 [m NAP]')
    assert rij.extra_lines == []


def test_faserow_extra_lines_gevuld() -> None:
    from reporting.builders.input_description_builder import FaseRow
    rij = FaseRow(
        label='Stempel',
        value='-1,0 [m NAP]',
        extra='15 graden t.o.v. maaiveld',
        extra_lines=['3,5 m lengte'],
    )
    assert rij.extra_lines == ['3,5 m lengte']
