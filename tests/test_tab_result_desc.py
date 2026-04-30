"""Tests voor TabResultDesc._maak_styled_tabel — groepkoppenrij."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ui.tabs.tab_result_desc import TabResultDesc
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
    assert 'Maatgevende resultaten' in labels
    assert 'Msd = 210 kNm/m' in labels
    assert 'Urep BGT = 12 mm' in labels
    assert 'Fase 1 - Start' in labels
