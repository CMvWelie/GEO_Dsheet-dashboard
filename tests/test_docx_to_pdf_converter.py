"""Tests voor DocxToPdfConverter."""

from __future__ import annotations
from unittest.mock import patch

from app.docx_to_pdf_converter import DocxToPdfConverter


def test_no_engines_when_nothing_available():
    """Als geen engine beschikbaar is, is available_engines leeg."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=False), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        assert conv.available_engines() == []
        assert conv.is_available() is False


def test_docx2pdf_detected():
    """Als docx2pdf importeerbaar is, staat 'docx2pdf' in lijst."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=True), \
         patch('app.docx_to_pdf_converter._find_libreoffice', return_value=None):
        conv = DocxToPdfConverter()
        assert 'docx2pdf' in conv.available_engines()
        assert conv.is_available() is True


def test_libreoffice_detected():
    """Als soffice gevonden wordt, staat 'libreoffice' in lijst."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=False), \
         patch('app.docx_to_pdf_converter._find_libreoffice',
                return_value=r'C:\Program Files\LibreOffice\program\soffice.exe'):
        conv = DocxToPdfConverter()
        assert 'libreoffice' in conv.available_engines()
        assert conv.is_available() is True


def test_preferred_order_docx2pdf_first():
    """Als beide beschikbaar zijn, staat docx2pdf vooraan (Windows-default)."""
    with patch('app.docx_to_pdf_converter._has_docx2pdf', return_value=True), \
         patch('app.docx_to_pdf_converter._find_libreoffice',
                return_value='/usr/bin/soffice'):
        conv = DocxToPdfConverter()
        assert conv.available_engines() == ['docx2pdf', 'libreoffice']
