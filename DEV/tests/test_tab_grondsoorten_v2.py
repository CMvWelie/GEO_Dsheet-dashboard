"""Tests voor de Grondsoortentabel v2-tab."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget

from parsers.models import FileBundle, Project, Soil, SoilLayer, SoilProfile, Stage
from ui.tabs.tab_grondsoorten_v2 import TabGrondsoortenv2


def _soil(naam: str) -> Soil:
    return Soil(
        name=naam,
        color='rgb(0,0,0)',
        color_int=None,
        gamma_dry=18.0,
        gamma_wet=20.0,
        cohesion=1.0,
        phi=32.0,
        delta=16.0,
        kh1=10.0,
        kh2=20.0,
        kh3=30.0,
    )


def _profiel(naam: str) -> SoilProfile:
    return SoilProfile(
        name=naam,
        normalized_name=naam.lower(),
        occurrence=1,
        x=None,
        y=None,
        layers=[
            SoilLayer(nr=1, level=0.0, wosp_top=0.0, wosp_bottom=0.0, material='Zand'),
        ],
    )


def _project(stages: list[Stage]) -> Project:
    links = _profiel('Links')
    rechts = SoilProfile(
        name='Rechts',
        normalized_name='rechts',
        occurrence=1,
        x=None,
        y=None,
        layers=[
            SoilLayer(nr=1, level=-1.0, wosp_top=0.0, wosp_bottom=0.0, material='Zand'),
        ],
    )
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=[_soil('Zand')],
        profiles=[links, rechts],
        stages=stages,
    )


def _content_widgets(tab: TabGrondsoortenv2) -> list[QWidget]:
    widgets = []
    for index in range(tab._content_layout.count() - 1):
        item = tab._content_layout.itemAt(index)
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def _label_teksten(tab: TabGrondsoortenv2) -> list[str]:
    return [label.text() for label in tab.findChildren(QLabel)]


def test_v2_tab_toont_enkelvoudige_fase_intro(qapp) -> None:
    tab = TabGrondsoortenv2()
    project = _project([Stage(name='Fase 1', left_profile='Links')])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert 'Grondlaagopbouw fases' in teksten
    assert 'Grondlagen fase: "Fase 1"' not in teksten
    assert 'In de fase "Fase 1" wordt het volgende profiel gehanteerd:' in teksten


def test_v2_tab_lijnt_laagkoppen_links_uit(qapp) -> None:
    tab = TabGrondsoortenv2()
    project = _project([Stage(name='Fase 1', left_profile='Links')])

    tab.populate(project)

    laag_koppen = [
        label
        for label in tab.findChildren(QLabel)
        if label.text() == 'Laag' and 'font-size: 10px' in label.styleSheet()
    ]
    assert len(laag_koppen) >= 2
    assert all(
        label.alignment() & Qt.AlignmentFlag.AlignLeft
        for label in laag_koppen
    )


def test_v2_tab_toont_meerdere_fases_als_streepjesregels(qapp) -> None:
    tab = TabGrondsoortenv2()
    project = _project([
        Stage(name='Fase 1', left_profile='Links'),
        Stage(name='Fase 2', left_profile='Links'),
    ])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert 'Grondlagen fases: "Fase 1" & "Fase 2"' not in teksten
    assert 'Het volgende profiel wordt gehanteerd in de volgende fases:' in teksten
    assert '- Fase 1' in teksten
    assert '- Fase 2' in teksten
    widgets = _content_widgets(tab)
    laatste_bullet_index = next(
        index
        for index, widget in enumerate(widgets)
        if isinstance(widget, QLabel) and widget.text() == '- Fase 2'
    )
    assert not isinstance(widgets[laatste_bullet_index + 1], QLabel)
    assert widgets[laatste_bullet_index + 1].height() == 8


def test_v2_tab_toont_grondlaagopbouwkop_alleen_bij_eerste_tabel(qapp) -> None:
    tab = TabGrondsoortenv2()
    project = _project([
        Stage(name='Fase 1', left_profile='Links'),
        Stage(name='Fase 2', left_profile='Rechts'),
    ])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert teksten.count('Grondlaagopbouw fases') == 1
    assert 'In de fase "Fase 1" wordt het volgende profiel gehanteerd:' in teksten
    assert 'In de fase "Fase 2" wordt het volgende profiel gehanteerd:' in teksten
    widgets = _content_widgets(tab)
    tweede_intro_index = next(
        index
        for index, widget in enumerate(widgets)
        if isinstance(widget, QLabel)
        and widget.text() == 'In de fase "Fase 2" wordt het volgende profiel gehanteerd:'
    )
    assert not isinstance(widgets[tweede_intro_index - 1], QLabel)
    assert widgets[tweede_intro_index - 1].height() == 8
    assert not isinstance(widgets[tweede_intro_index + 1], QLabel)
    assert widgets[tweede_intro_index + 1].height() == 8
