"""Tests voor TabResultDesc._maak_styled_tabel — groepkoppenrij."""

from __future__ import annotations

from PyQt6.QtWidgets import QGridLayout, QLabel
from PyQt6.QtCore import Qt

from ui.tabs.tab_result_desc import TabResultDesc
from parsers.models import (
    FileBundle,
    Project,
    ResultPoint,
    ResultStage,
    ResultStep,
    ResultSummary,
    SheetPilingElement,
)
from reporting.models import (
    ReportImageGroup,
    ReportImageRequest,
    ReportSection,
    ReportTable,
)


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


def _project_met_resultaten() -> Project:
    stap_64 = ResultStep(
        raw_step='CUR 166 6.4',
        stages={
            1: ResultStage(
                stage_number=1,
                points=[ResultPoint(depth=-1.0, moment=100.0, shear=50.0, disp=2.0)],
            )
        },
    )
    stap_65 = ResultStep(
        raw_step='CUR 166 6.5',
        stages={
            1: ResultStage(
                stage_number=1,
                points=[ResultPoint(depth=-1.0, moment=10.0, shear=5.0, disp=8.0)],
            )
        },
    )
    return Project(
        base_name='test',
        project_name='Test',
        file_bundle=FileBundle(),
        sheet_piling=[
            SheetPilingElement(
                name='AZ 18 (S240GP)',
                x=0.0,
                bottom=-12.0,
                top=1.0,
                width=1.0,
                opneembaar_moment_knm=250.0,
                steel_quality='S240GP',
            )
        ],
        result_summaries=[
            ResultSummary(
                stage_number=1,
                max_moment_knm=100.0,
                max_shear_kn=50.0,
                max_disp_mm=10.0,
                mob_moment_pct=60.0,
                mob_grond_pct=70.0,
            )
        ],
        result_steps={
            'CUR 166 6.4': stap_64,
            'CUR 166 6.5': stap_65,
        },
    )


def _gridpositie_voor_label(widget, tekst: str) -> tuple[int, int, int, int] | None:
    for grid in widget.findChildren(QGridLayout):
        for index in range(grid.count()):
            item = grid.itemAt(index)
            label = item.widget()
            if isinstance(label, QLabel) and label.text() == tekst:
                return grid.getItemPosition(index)
    return None


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


def test_specificatietabel_koprijen_spannen_volledige_breedte(qapp) -> None:
    """Koprijen in de specificatietabel vullen alle drie de tabelkolommen."""
    tab = TabResultDesc()
    tab.populate_resultaat_tabel(_project_met_resultaten())

    assert _gridpositie_voor_label(tab, 'Grondkering') == (0, 0, 1, 3)
    assert _gridpositie_voor_label(tab, 'Resultaten') == (7, 0, 1, 3)
    assert _gridpositie_voor_label(tab, 'Verificatiestap') == (7, 3, 1, 1)
    assert _gridpositie_voor_label(tab, 'stap 6.4') == (8, 3, 1, 1)


def test_resultaattab_toont_moederbestand_resultaten_intro(qapp) -> None:
    """De resultaat-tab start met de hoofdstuktitel en intro uit het moederbestand."""
    tab = TabResultDesc()
    tab.populate_resultaat_tabel(_project_met_resultaten())

    labels = [w.text() for w in tab.findChildren(QLabel)]
    assert 'Resultaten' in labels
    assert any('verificatiestappen volgens de CUR166' in tekst for tekst in labels)


def test_reporttabel_gebruikt_theme_fontgroottes(qapp) -> None:
    """ReportTable-labels gebruiken pt-groottes uit de centrale theme-tabelstijl."""
    tab = TabResultDesc()
    widget = tab._maak_styled_tabel(_tabel_met_groepen())

    labels = {w.text(): w.styleSheet() for w in widget.findChildren(QLabel)}
    assert 'font-size: 8pt' in labels['Momenten (kNm)']
    assert 'font-size: 8pt' in labels['Fase']
    assert 'font-size: 7pt' in labels['Fase 1']


def test_figuurtabel_gebruikt_theme_fontgroottes(qapp) -> None:
    """Figuurtabelkoppen en voetregels gebruiken theme-gedreven tabelgroottes."""
    tab = TabResultDesc()
    groep = ReportImageGroup(
        id='figuren',
        title='',
        headers=['Msd = 210 kNm/m', 'Dsd = 95 kN/m', 'Urep BGT = 12 mm'],
        images=[None, None, None],
        footers=['Fase 1 - Start', 'Fase 2 - Eind', 'Fase 2 - Eind'],
    )

    widget = tab._maak_figuurgroep_widget(groep)
    labels = {w.text(): w.styleSheet() for w in widget.findChildren(QLabel)}
    assert 'font-size: 8pt' in labels['Msd = 210 kNm/m']
    assert 'font-size: 7pt' in labels['Fase 1 - Start']


def test_populate_toont_extremen_figuurgroep_onderaan(qapp) -> None:
    """De 3x3 figuurtabel voor maatgevende resultaten verschijnt in de tab."""
    tab = TabResultDesc()
    img = ReportImageRequest(
        id='m',
        caption='',
        figure_key='moment_curve',
        stage_index=0,
        step_key='CUR 166 6.4',
    )
    sec = ReportSection(
        id='extremen_overzicht',
        title='Maatgevende resultaten',
        image_groups=[
            ReportImageGroup(
                id='extremen_3x3',
                title='',
                headers=['Msd = 210 kNm/m', 'Dsd = 95 kN/m', 'Urep BGT = 12 mm'],
                images=[img, None, None],
                footers=['Fase 1 - Start', 'Fase 2 - Eind', 'Fase 2 - Eind'],
            )
        ],
    )

    tab.populate([sec])

    labels = [w.text() for w in tab.findChildren(QLabel)]
    assert 'Maatgevende resultaten' not in labels
    assert any('grafische weergave van de maatgevende resultaten' in tekst for tekst in labels)
    assert 'Msd = 210 kNm/m' in labels
    assert 'Urep BGT = 12 mm' in labels
    assert 'Fase 1 - Start' in labels
