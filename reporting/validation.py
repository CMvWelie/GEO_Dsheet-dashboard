"""ReportValidator — valideert een ReportPackage voor export."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from reporting.models import ReportPackage


@dataclass
class ValidationIssue:
    field: str
    severity: Literal['error', 'warning']
    message: str


class ReportValidator:
    """Controleert een ReportPackage op volledigheid en consistentie."""

    REQUIRED_METADATA = [
        ('project_name', 'Projectnaam'),
        ('title', 'Rapporttitel'),
        ('author', 'Auteur'),
        ('date', 'Datum'),
    ]

    def validate(self, package: ReportPackage) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        self._check_metadata(package, issues)
        self._check_items(package, issues)
        self._check_templates(package, issues)
        return issues

    # ------------------------------------------------------------------

    def _check_metadata(self, package: ReportPackage,
                         issues: list[ValidationIssue]) -> None:
        for attr, label in self.REQUIRED_METADATA:
            if not getattr(package.metadata, attr, ''):
                issues.append(ValidationIssue(
                    field=f'metadata.{attr}',
                    severity='error',
                    message=f'{label} is verplicht maar niet ingevuld.',
                ))

    def _check_items(self, package: ReportPackage,
                      issues: list[ValidationIssue]) -> None:
        excel_items = [i for i in package.selected_items if i.included_excel]
        word_items = [i for i in package.selected_items if i.included_word]
        if not package.selected_items:
            issues.append(ValidationIssue(
                field='selected_items',
                severity='warning',
                message='Geen rapportage-items geselecteerd.',
            ))
        elif not excel_items and not word_items:
            issues.append(ValidationIssue(
                field='selected_items',
                severity='warning',
                message='Alle items zijn uitgesloten van Excel- én Word-export.',
            ))

    def _check_templates(self, package: ReportPackage,
                          issues: list[ValidationIssue]) -> None:
        for attr, label in [('template_excel', 'Excel-template'),
                             ('template_word', 'Word-template')]:
            path = getattr(package, attr, None)
            if path and not Path(path).exists():
                issues.append(ValidationIssue(
                    field=attr,
                    severity='error',
                    message=f'{label} bestand niet gevonden: {path}',
                ))
