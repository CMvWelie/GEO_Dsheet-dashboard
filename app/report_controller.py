"""ReportController — orkestreert rapportagelaag voor D-Sheet Dashboard.

Heeft geen Qt-kennis. Retourneert primitieven of domeinobjecten.
"""

from __future__ import annotations

from app.state import AppState
from app.report_state import ReportState
from reporting.models import ReportSection, ReportPackage
from reporting.selection import ReportPlan
from reporting.builders.input_description_builder import InputDescriptionBuilder, DamwandCard
from reporting.builders.result_description_builder import ResultDescriptionBuilder
from reporting.builders.soil_table_builder import SoilTableBuilder
from exporters.excel_exporter import ExcelExporter
from exporters.word_exporter import WordExporter


class ReportController:
    """Applicatielaag voor rapportage: builders, plan, exporters, validatie."""

    def __init__(self, app_state: AppState, report_state: ReportState) -> None:
        self._app = app_state
        self._report = report_state
        self._input_builder = InputDescriptionBuilder()
        self._result_builder = ResultDescriptionBuilder()
        self._soil_builder = SoilTableBuilder()
        self._excel = ExcelExporter()
        self._word = WordExporter()

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

    def build_input_descriptions(self) -> list[ReportSection]:
        """Bouw invoerbeschrijvingssecties voor actief project/fase."""
        project = self._app.get_active_project()
        stage = self._app.get_active_stage()
        if not project or not stage:
            return []
        return self._input_builder.build(project, stage, self._report.overrides)

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

    def build_soil_sections(self) -> list[ReportSection]:
        """Bouw grondsoortentabelsecties voor het actieve project.

        Returns
        -------
        list[ReportSection]
            Één sectie per grondprofiel, lege lijst als er geen project is.
        """
        project = self._app.get_active_project()
        if not project:
            return []
        return self._soil_builder.build(project)

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def set_template_excel(self, path: str | None) -> None:
        """Sla het Excel-templatepad op."""
        self._report.template_excel = path or None

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

    def get_plan(self) -> ReportPlan:
        """Geef het huidige rapportageplan terug."""
        return self._report.plan

    def auto_populate_plan(self) -> None:
        """Vul het rapportplan automatisch met items vanuit de builders.

        Voegt alleen items toe die er nog niet in zitten (op id).
        """
        from reporting.models import ReportItem
        input_secs = self.build_input_descriptions()
        result_secs = self.build_result_descriptions()
        for sec in input_secs:
            self._report.plan.add_item(ReportItem(
                id=f'input_{sec.id}',
                kind='invoer',
                caption=sec.title,
                source_ref=sec.id,
            ))
        for sec in result_secs:
            self._report.plan.add_item(ReportItem(
                id=f'result_{sec.id}',
                kind='resultaat',
                caption=sec.title,
                source_ref=sec.id,
            ))
        soil_secs = self.build_soil_sections()
        for sec in soil_secs:
            self._report.plan.add_item(ReportItem(
                id=f'grondsoorten_{sec.id}',
                kind='grondsoorten',
                caption=sec.title,
                source_ref=sec.id,
            ))

    # ------------------------------------------------------------------
    # Pakketbouw
    # ------------------------------------------------------------------

    def build_package(self) -> ReportPackage:
        """Bouw een ReportPackage op basis van huidige state."""
        input_secs = self.build_input_descriptions()
        result_secs = self.build_result_descriptions()
        soil_secs = self.build_soil_sections()
        pkg = self._report.plan.build_package(
            self._report.metadata, input_secs, result_secs,
            extra_sections=soil_secs,
        )
        pkg.template_excel = self._report.template_excel
        pkg.template_word = self._report.template_word
        return pkg

    def build_metadata(self) -> 'ReportMetadata':
        """Geef ReportMetadata op basis van de huidige rapport-state."""
        from reporting.models import ReportMetadata
        rs = self._report
        return ReportMetadata(
            project_name=getattr(rs, 'project_name', '') or '',
            client=getattr(rs, 'client', '') or '',
            author=getattr(rs, 'author', '') or '',
            date=getattr(rs, 'date', '') or '',
            revision=getattr(rs, 'revision', '') or '',
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_excel(self, output_path: str) -> str | None:
        """Exporteer naar Excel.

        Returns:
            None bij succes, foutmelding bij een fout.
        """
        package = self.build_package()
        return self._excel.export(package, self._report.template_excel, output_path)

    def export_word(self, output_path: str) -> str | None:
        """Exporteer naar Word.

        Gebruikt als template (in volgorde van prioriteit):
        1. Het pad ingevuld in TabWordExport (ReportState.template_word)
        2. Het persistente pad uit AppSettings (AppState.app_settings.word_template_path)
        3. Geen template (leeg document)

        Returns
        -------
        str | None
            None bij succes, foutmelding bij een fout.
        """
        package = self.build_package()
        template = (
            self._report.template_word
            or self._app.app_settings.word_template_path
            or None
        )
        return self._word.export(package, template, output_path)
