"""Tests voor de grondsoortentabel-tab."""
from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QComboBox, QFrame, QWidget

from parsers.models import FileBundle, Project, Soil, SoilLayer, SoilProfile
from ui.tabs.tab_grondsoorten import TabGrondsoorten


def _maak_project(profielen: list[SoilProfile] | None = None) -> Project:
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=[
            Soil(
                name='Zand',
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
            ),
        ],
        profiles=profielen or [],
    )


def _maak_profiel(naam: str) -> SoilProfile:
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


def _content_widgets(tab: TabGrondsoorten) -> list[QWidget]:
    widgets = []
    for index in range(tab._content_layout.count() - 1):
        item = tab._content_layout.itemAt(index)
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def test_populate_toont_alle_profielen_onder_elkaar(qapp) -> None:
    tab = TabGrondsoorten()
    project = _maak_project([
        _maak_profiel('Links'),
        _maak_profiel('Rechts'),
    ])

    tab.populate(project)

    widgets = _content_widgets(tab)
    assert len(widgets) == 5
    assert isinstance(widgets[0], QLabel)
    assert isinstance(widgets[1], QLabel)
    assert widgets[1].text() == '1* — Links'
    assert isinstance(widgets[2], QFrame)
    assert isinstance(widgets[3], QLabel)
    assert widgets[3].text() == '2* — Rechts'
    assert isinstance(widgets[4], QFrame)


def test_profiel_dropdown_is_verwijderd(qapp) -> None:
    tab = TabGrondsoorten()

    assert tab.findChildren(QComboBox) == []


def test_populate_zonder_project_toont_lege_state(qapp) -> None:
    tab = TabGrondsoorten()

    tab.populate(None)

    widgets = _content_widgets(tab)
    assert len(widgets) == 1
    assert isinstance(widgets[0], QLabel)
    assert widgets[0].text() == 'Geen profieldata beschikbaar. Laad een project.'
