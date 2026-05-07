"""ReportController — orkestreert rapportagelaag voor D-Sheet Dashboard.

Heeft geen Qt-kennis. Retourneert primitieven of domeinobjecten.
"""

from __future__ import annotations

from app.state import AppState
from app.report_state import ReportState
from reporting.models import ReportItem, ReportSection, ReportMetadata
from reporting.builders.damwand_hoofdstuk_builder import DamwandHoofdstukBuilder
from reporting.builders.input_description_builder import InputDescriptionBuilder, DamwandCard
from reporting.builders.result_description_builder import ResultDescriptionBuilder
from exporters.word_hoofdstuk_exporter import WordHoofdstukExporter


class ReportController:
    """Applicatielaag voor rapportage: builders, plan, exporters, validatie."""

    def __init__(self, app_state: AppState, report_state: ReportState) -> None:
        self._app = app_state
        self._report = report_state
        self._damwand_builder = DamwandHoofdstukBuilder()
        self._input_builder = InputDescriptionBuilder()
        self._result_builder = ResultDescriptionBuilder()

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def build_all_fase_cards(self):
        """Bouw FaseCard-lijst voor alle fases van het actieve project."""
        project = self._app.get_active_project()
        if not project:
            return []
        return self._input_builder.build_all_stages(project)

    def build_damwand_card(self) -> DamwandCard | None:
        """Bouw DamwandCard voor het actieve project."""
        project = self._app.get_active_project()
        if not project:
            return None
        return self._input_builder.build_damwand_card(project)

    def build_result_descriptions(self) -> list[ReportSection]:
        """Bouw resultaatbeschrijvingssecties voor actief project/fase/stap."""
        project = self._app.get_active_project()
        if not project:
            return []
        return self._result_builder.build(
            project,
            self._app.active_output_stage_index,
            self._app.active_result_step,
            self._report.overrides,
        )

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def set_template_word(self, path: str | None) -> None:
        """Sla het Word-templatepad op."""
        self._report.template_word = path or None

    # ------------------------------------------------------------------
    # Overrides (stap 9)
    # ------------------------------------------------------------------

    def set_text_override(self, block_id: str, text: str) -> None:
        """Sla een handmatige tekstoverride op (leeg = verwijder override)."""
        if text.strip():
            self._report.overrides[block_id] = text
        else:
            self._report.overrides.pop(block_id, None)

    # ------------------------------------------------------------------
    # Plan
    # ------------------------------------------------------------------

    def auto_populate_plan(self) -> None:
        """Vul het rapportplan automatisch met secties van DamwandHoofdstukBuilder.

        Het bestaande plan wordt eerst leeggemaakt zodat de lijst altijd het
        actieve project weerspiegelt.
        """
        project = self._app.get_active_project()
        if not project:
            self._report.plan.items.clear()
            return
        self._report.plan.items.clear()
        secties = self._damwand_builder.build(project, None, None)
        gewenste_ids: list[str] = []
        for sec in secties:
            gewenste_ids.append(sec.id)
            self._report.plan.add_item(ReportItem(
                id=sec.id,
                kind=self._sectie_kind(sec.id),
                caption=sec.title,
                source_ref=sec.id,
            ))
        self._orden_plan_items(gewenste_ids)

    _RESULTAAT_IDS: frozenset[str] = frozenset({
        'anchor_forces', 'per_phase_summary', 'extremen_overzicht',
    })

    def _sectie_kind(self, sec_id: str) -> str:
        if sec_id in self._RESULTAAT_IDS:
            return 'resultaat'
        if sec_id.startswith('grondsoorten'):
            return 'grondsoorten'
        return 'invoer'

    def _orden_plan_items(self, gewenste_ids: list[str]) -> None:
        """Orden bestaande planitems volgens de opgegeven id-volgorde."""
        volgorde = {item_id: i for i, item_id in enumerate(gewenste_ids)}
        self._report.plan.items.sort(
            key=lambda item: (volgorde.get(item.id, len(volgorde)), item.order)
        )
        self._report.plan._renumber()

    def build_metadata(self) -> ReportMetadata:
        """Geef ReportMetadata op basis van de huidige rapport-state."""
        return self._report.metadata

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_word(self, output_path: str) -> str | None:
        """Exporteer naar Word via WordHoofdstukExporter.

        Returns
        -------
        str | None
            None bij succes, foutmelding bij een fout.
        """
        project = self._app.get_active_project()
        if not project:
            return 'Geen actief project geladen.'
        alle_secties = self._damwand_builder.build(project, None, None)
        geselecteerd = {
            item.source_ref for item in self._report.plan.items if item.included_word
        }
        secties = [s for s in alle_secties if s.id in geselecteerd] if geselecteerd else alle_secties
        metadata = self.build_metadata()
        template = (
            self._report.template_word
            or self._app.app_settings.word_template_path
            or 'templates/damwand_stijlen.docx'
        )
        return WordHoofdstukExporter().export(
            sections=secties,
            metadata=metadata,
            project=project,
            template_path=template,
            output_path=output_path,
        )
