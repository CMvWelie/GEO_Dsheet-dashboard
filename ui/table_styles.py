"""Centrale tabelstijlen voor rapport- en debugtabellen."""

from __future__ import annotations

import sys

from app.theme import Theme


TABLE_HEADER_BG = '#147ACF'
TABLE_HEADER_FG = '#FFFFFF'
TABLE_HEADER_SUB_BG = TABLE_HEADER_BG
TABLE_HEADER_SUB_FG = TABLE_HEADER_FG
TABLE_BORDER = '#000000'
TABLE_ROW_SEP = TABLE_BORDER
TABLE_ROW_ODD_BG = '#FFFFFF'
TABLE_ROW_EVEN_BG = '#F2F2F2'
TABLE_LABEL_COLOR = '#000000'
TABLE_VALUE_COLOR = '#000000'
TABLE_EXTRA_COLOR = '#000000'
TABLE_FONT = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'

def configure_from_theme(theme: Theme | None) -> None:
    """Werk de centrale tabelstijl bij vanuit het actieve UI-thema."""
    if theme is None:
        return

    global TABLE_HEADER_BG, TABLE_HEADER_FG, TABLE_HEADER_SUB_BG, TABLE_HEADER_SUB_FG
    global TABLE_BORDER, TABLE_ROW_SEP, TABLE_ROW_ODD_BG, TABLE_ROW_EVEN_BG
    global TABLE_LABEL_COLOR, TABLE_VALUE_COLOR, TABLE_EXTRA_COLOR, TABLE_FONT
    global REPORT_QTABLE_STYLE, BASIC_DEBUG_QTABLE_STYLE

    table = theme.table
    TABLE_HEADER_BG = table.header_bg
    TABLE_HEADER_FG = table.header_fg
    TABLE_HEADER_SUB_BG = table.subheader_bg
    TABLE_HEADER_SUB_FG = table.subheader_fg
    TABLE_BORDER = table.border
    TABLE_ROW_SEP = table.border
    TABLE_ROW_ODD_BG = table.row_odd_bg
    TABLE_ROW_EVEN_BG = table.row_even_bg
    TABLE_LABEL_COLOR = table.label_color
    TABLE_VALUE_COLOR = table.value_color
    TABLE_EXTRA_COLOR = table.extra_color
    TABLE_FONT = f'"{theme.typography.family}", "{theme.typography.fallback}", sans-serif'
    REPORT_QTABLE_STYLE = build_report_qtable_style()
    BASIC_DEBUG_QTABLE_STYLE = build_debug_qtable_style()
    _sync_loaded_legacy_aliases()


def build_report_qtable_style() -> str:
    return f"""
QTableWidget {{
    background: {TABLE_ROW_ODD_BG};
    alternate-background-color: {TABLE_ROW_EVEN_BG};
    gridline-color: {TABLE_BORDER};
    border: 1px solid {TABLE_BORDER};
    font-family: {TABLE_FONT};
    font-size: 11px;
}}

QHeaderView::section {{
    background: {TABLE_HEADER_BG};
    color: {TABLE_HEADER_FG};
    border: 1px solid {TABLE_BORDER};
    padding: 4px 6px;
    font-weight: 700;
}}

QTableWidget::item {{
    padding: 2px 6px;
}}
""".strip()

def build_debug_qtable_style() -> str:
    return f"""
QTableWidget {{
    background: #FFFFFF;
    alternate-background-color: #F7F7F7;
    gridline-color: #808080;
    border: 1px solid #808080;
    font-family: {TABLE_FONT};
    font-size: 11px;
}}

QHeaderView::section {{
    background: #F0F0F0;
    color: #000000;
    border: 1px solid #808080;
    padding: 3px 6px;
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 2px 6px;
}}
""".strip()


def report_qtable_style() -> str:
    """Geef de huidige stylesheet voor rapporttabellen."""
    return build_report_qtable_style()


def debug_qtable_style() -> str:
    """Geef de huidige stylesheet voor debugtabellen."""
    return build_debug_qtable_style()


REPORT_QTABLE_STYLE = build_report_qtable_style()
BASIC_DEBUG_QTABLE_STYLE = build_debug_qtable_style()


def _sync_loaded_legacy_aliases() -> None:
    """Werk oude module-globals bij voor tabs die tabelconstanten hebben gekopieerd."""
    aliases = {
        '_HDR_BG': TABLE_HEADER_BG,
        '_HDR_FG': TABLE_HEADER_FG,
        '_SUBHDR_BG': TABLE_HEADER_SUB_BG,
        '_SUBHDR_FG': TABLE_HEADER_SUB_FG,
        '_BORDER': TABLE_BORDER,
        '_ROW_SEP': TABLE_ROW_SEP,
        '_ROW_ODD_BG': TABLE_ROW_ODD_BG,
        '_ROW_EVN_BG': TABLE_ROW_EVEN_BG,
        '_ROW_EVEN_BG': TABLE_ROW_EVEN_BG,
        '_LABEL_CLR': TABLE_LABEL_COLOR,
        '_VALUE_CLR': TABLE_VALUE_COLOR,
        '_EXTRA_CLR': TABLE_EXTRA_COLOR,
        '_FONT': TABLE_FONT,
        'REPORT_QTABLE_STYLE': REPORT_QTABLE_STYLE,
        'BASIC_DEBUG_QTABLE_STYLE': BASIC_DEBUG_QTABLE_STYLE,
    }
    for module_name in (
        'ui.info_panel',
        'ui.layer_table',
        'ui.tabs.tab_debug_invoer',
        'ui.tabs.tab_debug_uitvoer',
        'ui.tabs.tab_grondsoorten',
        'ui.tabs.tab_input_desc',
        'ui.tabs.tab_result_desc',
        'ui.tabs.tab_verticaal_evenwicht',
    ):
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for name, value in aliases.items():
            if hasattr(module, name):
                setattr(module, name, value)
