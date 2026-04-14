"""Tests voor HtmlPreviewBuilder."""

from __future__ import annotations

from reporting.builders.html_preview_builder import HtmlPreviewBuilder
from reporting.models import (
    ReportPackage, ReportMetadata, ReportSection,
    ReportField, ReportTable, ReportItem, TextBlock,
)


def _maak_package_met_sectie() -> tuple[ReportPackage, ReportSection]:
    sec = ReportSection(id='damwand', title='Damwand')
    sec.fields.append(ReportField('top', 'Bovenzijde', '0,00', 'm NAP'))
    sec.fields.append(ReportField('bot', 'Onderzijde', '-12,50', 'm NAP'))
    item = ReportItem(
        id='input_damwand', kind='invoer', caption='Damwand', source_ref='damwand'
    )
    pkg = ReportPackage(
        metadata=ReportMetadata(project_name='Testproject'),
        input_sections=[sec],
        selected_items=[item],
    )
    return pkg, sec


def test_lege_package_bevat_geen_secties_melding() -> None:
    """Lege package → melding 'Geen secties geselecteerd'."""
    html = HtmlPreviewBuilder().build(ReportPackage())
    assert 'Geen secties geselecteerd' in html


def test_projectnaam_zichtbaar_in_html() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Testproject' in html


def test_geselecteerde_sectietitel_zichtbaar() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Damwand' in html


def test_velden_zichtbaar_in_html() -> None:
    pkg, _ = _maak_package_met_sectie()
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Bovenzijde' in html
    assert '0,00' in html
    assert 'm NAP' in html


def test_niet_geselecteerde_sectie_niet_zichtbaar() -> None:
    sec = ReportSection(id='water', title='Waterpeilen')
    pkg = ReportPackage(input_sections=[sec], selected_items=[])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Waterpeilen' not in html


def test_tabel_weergegeven_als_html_tabel() -> None:
    tbl = ReportTable(
        id='ankers', title='Ankers',
        columns=['Naam', 'Niveau [m NAP]'],
        rows=[['Anker-1', '-3,50'], ['Anker-2', '-4,00']],
    )
    sec = ReportSection(id='anchors', title='Ankers', tables=[tbl])
    item = ReportItem(id='input_anchors', kind='invoer', caption='Ankers', source_ref='anchors')
    pkg = ReportPackage(input_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert '<table' in html.lower()
    assert 'Anker-1' in html
    assert '-3,50' in html


def test_tekstblok_effective_text_zichtbaar() -> None:
    sec = ReportSection(id='sec', title='Sectie')
    sec.text_blocks.append(TextBlock(
        id='blk', section='sec',
        generated_text='Gegenereerde tekst.',
        manual_override='Handmatige override.',
    ))
    item = ReportItem(id='input_sec', kind='invoer', caption='Sectie', source_ref='sec')
    pkg = ReportPackage(input_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Handmatige override.' in html
    assert 'Gegenereerde tekst.' not in html


def test_resultaat_sectie_opgenomen_bij_kind_resultaat() -> None:
    sec = ReportSection(id='moment', title='Momentendiagram')
    sec.fields.append(ReportField('max', 'Max. moment', '142,3', 'kNm/m'))
    item = ReportItem(
        id='result_moment', kind='resultaat', caption='Momenten', source_ref='moment'
    )
    pkg = ReportPackage(result_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Momentendiagram' in html
    assert '142,3' in html
