"""Tests voor de grondsoortentabel-tab."""
from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QComboBox, QFrame, QWidget

from parsers.models import FileBundle, Project, Soil, SoilLayer, SoilProfile, Stage
from ui.tabs.tab_grondsoorten import TabGrondsoorten, _is_enkelvoudig


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


def _maak_profiel(naam: str, materiaal: str = 'Zand') -> SoilProfile:
    return SoilProfile(
        name=naam,
        normalized_name=naam.lower(),
        occurrence=1,
        x=None,
        y=None,
        layers=[
            SoilLayer(nr=1, level=0.0, wosp_top=0.0, wosp_bottom=0.0, material=materiaal),
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
    # intro + sectiekop Ka/K0/Kp + Ka-tabel + 2× (profielkop + profieltabel) = 7
    assert len(widgets) == 7
    assert isinstance(widgets[0], QLabel)   # intro
    assert isinstance(widgets[1], QLabel)   # sectiekop 'Gronddrukcoëfficiënten'
    assert isinstance(widgets[2], QWidget)   # Ka/K0/Kp-tabel (in breedtewrapper)
    assert isinstance(widgets[3], QLabel)   # kop '1* — Links'
    assert widgets[3].text() == '1* — Links'
    assert isinstance(widgets[4], QFrame)   # profieltabel Links
    assert isinstance(widgets[5], QLabel)   # kop '2* — Rechts'
    assert widgets[5].text() == '2* — Rechts'
    assert isinstance(widgets[6], QFrame)   # profieltabel Rechts


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


def test_gelijke_rij_in_tweede_tabel_wordt_samengevoegd(qapp) -> None:
    tab = TabGrondsoorten()
    project = _maak_project([
        _maak_profiel('Links'),
        _maak_profiel('Rechts'),
    ])

    tab.populate(project)

    tweede_tabel = _content_widgets(tab)[6]
    teksten = [label.text() for label in tweede_tabel.findChildren(QLabel)]
    assert 'gelijk aan 1* \u2014 Links' in teksten


def test_gewijzigde_rij_in_tweede_tabel_blijft_uitgeschreven(qapp) -> None:
    tab = TabGrondsoorten()
    project = _maak_project([
        _maak_profiel('Links'),
        _maak_profiel('Rechts', materiaal='Klei'),
    ])

    tab.populate(project)

    tweede_tabel = _content_widgets(tab)[6]
    teksten = [label.text() for label in tweede_tabel.findChildren(QLabel)]
    assert 'gelijk aan 1* \u2014 Links' not in teksten
    assert 'Klei' in teksten


def _maak_stage(left: str, right: str | None = None) -> Stage:
    return Stage(name='Fase', left_profile=left, right_profile=right or left)


def _maak_project_met_stages(
    links_naam: str,
    rechts_naam: str,
    stages: list[Stage],
) -> Project:
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
    return Project(
        base_name='test',
        project_name='Test',
        file_bundle=FileBundle(),
        soils=[
            Soil(
                name='Zand', color='rgb(0,0,0)', color_int=None,
                gamma_dry=18.0, gamma_wet=20.0, cohesion=1.0,
                phi=32.0, delta=16.0, kh1=10.0, kh2=20.0, kh3=30.0,
            ),
        ],
        profiles=[_profiel(links_naam), _profiel(rechts_naam, level=-1.0)],
        stages=stages,
    )


def test_is_enkelvoudig_geen_stages() -> None:
    project = _maak_project([])
    assert _is_enkelvoudig(project) is True


def test_is_enkelvoudig_links_gelijk_aan_rechts() -> None:
    project = _maak_project_met_stages(
        'Links', 'Links',
        [_maak_stage('Links', 'Links')],
    )
    assert _is_enkelvoudig(project) is True


def test_is_enkelvoudig_links_ongelijk_aan_rechts() -> None:
    project = _maak_project_met_stages(
        'Links', 'Rechts',
        [_maak_stage('Links', 'Rechts')],
    )
    assert _is_enkelvoudig(project) is False


def test_is_enkelvoudig_wisselende_fasen() -> None:
    project = _maak_project_met_stages(
        'Links', 'Links',
        [
            _maak_stage('Links', 'Links'),
            Stage(name='Fase 2', left_profile='Links', right_profile='Links'),
        ],
    )
    assert _is_enkelvoudig(project) is True


def test_is_enkelvoudig_fasen_wisselen_profiel() -> None:
    def _profiel(naam: str, level: float) -> SoilProfile:
        return SoilProfile(
            name=naam, normalized_name=naam.lower(), occurrence=1,
            x=None, y=None,
            layers=[
                SoilLayer(nr=1, level=level, wosp_top=0.0, wosp_bottom=0.0, material='Zand'),
            ],
        )
    project = Project(
        base_name='test', project_name='Test',
        file_bundle=FileBundle(),
        soils=[
            Soil(
                name='Zand', color='rgb(0,0,0)', color_int=None,
                gamma_dry=18.0, gamma_wet=20.0, cohesion=1.0,
                phi=32.0, delta=16.0, kh1=10.0, kh2=20.0, kh3=30.0,
            ),
        ],
        profiles=[
            _profiel('Fase1Profiel', 0.0),
            _profiel('Fase2Profiel', -2.0),
        ],
        stages=[
            Stage(name='Fase 1', left_profile='Fase1Profiel', right_profile='Fase1Profiel'),
            Stage(name='Fase 2', left_profile='Fase2Profiel', right_profile='Fase2Profiel'),
        ],
    )
    assert _is_enkelvoudig(project) is False


def test_volledig_pad_toont_grondsoortenoverzicht_en_fases(qapp) -> None:
    """Project met L≠R → volledige v2-weergave."""
    tab = TabGrondsoorten()
    project = _maak_project_met_stages(
        'Links', 'Rechts',
        [Stage(name='Fase 1', left_profile='Links', right_profile='Rechts')],
    )

    tab.populate(project)

    teksten = [label.text() for label in tab.findChildren(QLabel)]
    assert 'Grondsoorten' in teksten
    assert 'Grondlaagopbouw fases' in teksten
    assert 'Grondlagen linkerzijde' in teksten


def test_enkelvoudig_pad_actief_bij_gelijke_zijden(qapp) -> None:
    """Project zonder stages → enkelvoudig pad → profielkop aanwezig."""
    tab = TabGrondsoorten()
    project = _maak_project([_maak_profiel('EénProfiel')])

    tab.populate(project)

    teksten = [label.text() for label in tab.findChildren(QLabel)]
    assert '1* — EénProfiel' in teksten
    assert 'Grondsoorten' not in teksten
