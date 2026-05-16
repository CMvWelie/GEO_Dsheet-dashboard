"""Tests voor het volledig pad van TabGrondsoorten (voorheen TabGrondsoortenv2)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QWidget

from parsers.models import FileBundle, Project, Soil, SoilLayer, SoilProfile, Stage
from ui.tabs.tab_grondsoorten import TabGrondsoorten


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


def _profiel(naam: str, level: float = 0.0) -> SoilProfile:
    return SoilProfile(
        name=naam,
        normalized_name=naam.lower(),
        occurrence=1,
        x=None,
        y=None,
        layers=[
            SoilLayer(nr=1, level=level, wosp_top=0.0, wosp_bottom=0.0, material='Zand'),
        ],
    )


def _project_lr(stages: list[Stage]) -> Project:
    """Project met twee verschillende profielen (L≠R → volledig pad)."""
    return Project(
        base_name='test',
        project_name='Testproject',
        file_bundle=FileBundle(),
        soils=[_soil('Zand')],
        profiles=[_profiel('Links'), _profiel('Rechts', level=-1.0)],
        stages=stages,
    )


def _content_widgets(tab: TabGrondsoorten) -> list[QWidget]:
    widgets = []
    for index in range(tab._content_layout.count() - 1):
        item = tab._content_layout.itemAt(index)
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def _label_teksten(tab: TabGrondsoorten) -> list[str]:
    return [label.text() for label in tab.findChildren(QLabel)]


def test_volledig_pad_toont_enkelvoudige_fase_intro(qapp) -> None:
    tab = TabGrondsoorten()
    project = _project_lr([Stage(name='Fase 1', left_profile='Links', right_profile='Rechts')])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert 'Grondlaagopbouw fases' in teksten
    assert 'In de fase "Fase 1" wordt het volgende profiel gehanteerd:' in teksten


def test_volledig_pad_lijnt_laagkoppen_links_uit(qapp) -> None:
    tab = TabGrondsoorten()
    project = _project_lr([Stage(name='Fase 1', left_profile='Links', right_profile='Rechts')])

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


def test_volledig_pad_toont_meerdere_fases_als_streepjesregels(qapp) -> None:
    tab = TabGrondsoorten()
    project = _project_lr([
        Stage(name='Fase 1', left_profile='Links', right_profile='Rechts'),
        Stage(name='Fase 2', left_profile='Links', right_profile='Rechts'),
    ])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert 'Het volgende profiel wordt gehanteerd in de volgende fases:' in teksten
    assert '- Fase 1' in teksten
    assert '- Fase 2' in teksten


def test_volledig_pad_toont_grondlaagopbouwkop_alleen_bij_eerste_tabel(qapp) -> None:
    tab = TabGrondsoorten()
    project = _project_lr([
        Stage(name='Fase 1', left_profile='Links', right_profile='Rechts'),
        Stage(name='Fase 2', left_profile='Rechts', right_profile='Links'),
    ])

    tab.populate(project)

    teksten = _label_teksten(tab)
    assert teksten.count('Grondlaagopbouw fases') == 1
    assert 'In de fase "Fase 1" wordt het volgende profiel gehanteerd:' in teksten
    assert 'In de fase "Fase 2" wordt het volgende profiel gehanteerd:' in teksten
