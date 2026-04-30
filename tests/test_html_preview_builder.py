"""Tests voor HtmlPreviewBuilder."""

from __future__ import annotations

from reporting.builders.html_preview_builder import HtmlPreviewBuilder
from reporting.builders import html_preview_builder
from reporting.models import (
    ReportImageGroup,
    ReportPackage, ReportMetadata, ReportSection,
    ReportField, ReportImageRequest, ReportTable, ReportItem, TextBlock,
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


def test_grondsoorten_sectie_opgenomen_bij_kind_grondsoorten() -> None:
    """kind='grondsoorten' → sectie uit extra_sections zichtbaar in HTML."""
    sec = ReportSection(id='soil_table_links', title='Grondsoortentabel \u2014 Links')
    tbl = ReportTable(
        id='t', title='',
        columns=['BK [m NAP]', 'Laag'],
        rows=[['-5,0', 'Zand']],
    )
    sec.tables.append(tbl)
    item = ReportItem(
        id='grondsoorten_soil_table_links',
        kind='grondsoorten',
        caption='Grondsoortentabel \u2014 Links',
        source_ref='soil_table_links',
    )
    pkg = ReportPackage(extra_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg)
    assert 'Grondsoortentabel' in html
    assert 'Zand' in html


def test_image_request_wordt_data_uri_met_caption(monkeypatch) -> None:
    """Figuurverzoeken worden als base64-afbeelding in HTML opgenomen."""
    monkeypatch.setattr(html_preview_builder, 'render_figuur', lambda _img, _project: b'png')
    sec = ReportSection(
        id='fase_1',
        title='Fase 1',
        images=[
            ReportImageRequest(
                id='fig_1',
                caption='Doorsnede fase 1',
                figure_key='section',
                stage_index=0,
                step_key=None,
            )
        ],
    )
    item = ReportItem(
        id='damwand_fase_1',
        kind='invoer',
        caption='Fase 1',
        source_ref='fase_1',
    )
    pkg = ReportPackage(input_sections=[sec], selected_items=[item])
    html = HtmlPreviewBuilder().build(pkg, project=object())
    assert 'data:image/png;base64,cG5n' in html
    assert 'Doorsnede fase 1' in html


def test_image_group_wordt_als_3x3_tabel_gerenderd(monkeypatch) -> None:
    """Een figuurgroep rendert headers, figuurcellen en bronregels in HTML."""
    monkeypatch.setattr(html_preview_builder, 'render_figuur', lambda _img, _project: b'png')
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
                images=[img, img, img],
                footers=['Fase 1 - Start', 'Fase 2 - Eind', 'Fase 2 - Eind'],
            )
        ],
    )
    item = ReportItem(
        id='result_extremen_overzicht',
        kind='resultaat',
        caption='Maatgevende resultaten',
        source_ref='extremen_overzicht',
    )
    pkg = ReportPackage(result_sections=[sec], selected_items=[item])

    html = HtmlPreviewBuilder().build(pkg, project=object())

    assert 'class="figuurgroep"' in html
    assert 'Msd = 210 kNm/m' in html
    assert html.count('data:image/png;base64,cG5n') == 3
    assert 'Fase 1 - Start' in html
