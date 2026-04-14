"""Domeinmodellen voor de rapportagelaag van D-Sheet Dashboard."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ReportField:
    key: str
    label: str
    value: str
    unit: str = ''


@dataclass
class ReportTable:
    id: str
    title: str
    columns: list[str]
    rows: list[list[str]]


@dataclass
class ReportImageRequest:
    id: str
    caption: str
    figure_key: str
    stage_index: int
    step_key: str | None


@dataclass
class TextBlock:
    id: str
    section: str
    generated_text: str
    manual_override: str | None = None
    source: str = ''

    @property
    def effective_text(self) -> str:
        return self.manual_override if self.manual_override is not None else self.generated_text


@dataclass
class ReportSection:
    id: str
    title: str
    fields: list[ReportField] = field(default_factory=list)
    tables: list[ReportTable] = field(default_factory=list)
    images: list[ReportImageRequest] = field(default_factory=list)
    text_blocks: list[TextBlock] = field(default_factory=list)


@dataclass
class ReportMetadata:
    client: str = ''
    project_name: str = ''
    onderdeel: str = ''
    author: str = ''
    date: str = ''
    revision: str = ''
    logo_path: str = ''
    # overige velden (niet getoond in UI, behouden voor exporters)
    order_number: str = ''
    location: str = ''
    phase: str = ''
    title: str = ''
    report_profile: str = 'default'


@dataclass
class ReportItem:
    id: str
    kind: str
    caption: str
    included_excel: bool = True
    included_word: bool = True
    order: int = 0
    source_ref: str = ''


@dataclass
class ReportPackage:
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    input_sections: list[ReportSection] = field(default_factory=list)
    result_sections: list[ReportSection] = field(default_factory=list)
    extra_sections: list[ReportSection] = field(default_factory=list)
    selected_items: list[ReportItem] = field(default_factory=list)
    template_excel: str | None = None
    template_word: str | None = None
