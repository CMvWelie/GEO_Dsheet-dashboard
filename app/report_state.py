"""ReportState — state voor rapportage (naast AppState)."""

from __future__ import annotations
from dataclasses import dataclass, field

from reporting.models import ReportMetadata
from reporting.selection import ReportPlan


@dataclass
class ReportState:
    metadata: ReportMetadata = field(default_factory=ReportMetadata)
    plan: ReportPlan = field(default_factory=ReportPlan)
    template_excel: str | None = None
    template_word: str | None = None
    overrides: dict[str, str] = field(default_factory=dict)  # text_block_id → override_text
