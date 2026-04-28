"""Tests voor TabResultDesc._maak_styled_tabel — groepkoppenrij."""

from __future__ import annotations

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
