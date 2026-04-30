"""Tests voor WordExporter."""

from __future__ import annotations

import base64
import os
import tempfile

from docx import Document

from exporters import word_exporter
from exporters.word_exporter import WordExporter
from reporting.models import (
    ReportImageGroup,
    ReportImageRequest,
    ReportItem,
    ReportMetadata,
    ReportPackage,
    ReportSection,
)


_PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwAD'
    'hgGAWjR9awAAAABJRU5ErkJggg=='
)


def test_word_exporter_schrijft_image_als_inline_shape(monkeypatch) -> None:
    """Een sectie met image-request geeft een inline shape in de docx."""
    monkeypatch.setattr(word_exporter, 'render_figuur', lambda _img, _project: _PNG_1X1)
    sec = ReportSection(
        id='fase_1',
        title='Fase 1',
        images=[
            ReportImageRequest(
                id='img_fase_1',
                caption='Doorsnede fase 1',
                figure_key='section',
                stage_index=0,
                step_key=None,
            )
        ],
    )
    pkg = ReportPackage(
        metadata=ReportMetadata(project_name='T'),
        input_sections=[sec],
        selected_items=[
            ReportItem(
                id='damwand_fase_1',
                kind='invoer',
                caption='Fase 1',
                source_ref='fase_1',
            )
        ],
    )
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as handle:
        out = handle.name
    fout = WordExporter().export(pkg, None, out, project=object())
    assert fout is None
    doc = Document(out)
    os.unlink(out)
    assert len(doc.inline_shapes) == 1


def test_word_exporter_schrijft_image_group_als_tabel(monkeypatch) -> None:
    """Een 3x3 figuurgroep wordt als Word-tabel met drie afbeeldingen geschreven."""
    monkeypatch.setattr(word_exporter, 'render_figuur', lambda _img, _project: _PNG_1X1)
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
    pkg = ReportPackage(
        metadata=ReportMetadata(project_name='T'),
        result_sections=[sec],
        selected_items=[
            ReportItem(
                id='result_extremen_overzicht',
                kind='resultaat',
                caption='Maatgevende resultaten',
                source_ref='extremen_overzicht',
            )
        ],
    )
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as handle:
        out = handle.name
    fout = WordExporter().export(pkg, None, out, project=object())
    assert fout is None
    doc = Document(out)
    os.unlink(out)
    assert len(doc.tables) == 2
    assert len(doc.inline_shapes) == 3
    assert doc.tables[-1].rows[0].cells[0].text == 'Msd = 210 kNm/m'
