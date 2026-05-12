"""SessionData — projectsessie-dataclasse voor .dsd-bestanden."""

from __future__ import annotations

from dataclasses import dataclass, field

from reporting.models import ReportItem, ReportMetadata


@dataclass
class SessionData:
    """Alle projectspecifieke data die in een .dsd-sessiebestand wordt opgeslagen.

    Parameters
    ----------
    version:
        Formaatversie, verhoog bij brekende wijzigingen.
    source_paths:
        Absolute paden naar de .shd-bronbestanden.
    report_metadata:
        Rapportmetadata (opdrachtgever, projectnaam, auteur, etc.).
    report_overrides:
        Tekstblokoverschrijvingen: block_id → overschreven tekst.
    report_plan_items:
        Geselecteerde en geordende rapportitems.
    """

    version: int = 1
    source_paths: list[str] = field(default_factory=list)
    report_metadata: ReportMetadata = field(default_factory=ReportMetadata)
    report_overrides: dict[str, str] = field(default_factory=dict)
    report_plan_items: list[ReportItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialiseer naar een JSON-compatibel dict."""
        return {
            'version': self.version,
            'source_paths': self.source_paths,
            'report_metadata': {
                f: getattr(self.report_metadata, f)
                for f in self.report_metadata.__dataclass_fields__
            },
            'report_overrides': self.report_overrides,
            'report_plan_items': [
                {f: getattr(item, f) for f in item.__dataclass_fields__}
                for item in self.report_plan_items
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> SessionData:
        """Deserialiseer vanuit een JSON-dict; ontbrekende sleutels krijgen defaults."""
        meta_data = d.get('report_metadata', {})
        if meta_data:
            meta = ReportMetadata(**{
                k: v for k, v in meta_data.items()
                if k in ReportMetadata.__dataclass_fields__
            })
        else:
            meta = ReportMetadata()

        items_data = d.get('report_plan_items', [])
        items = [
            ReportItem(**{
                k: v for k, v in item.items()
                if k in ReportItem.__dataclass_fields__
            })
            for item in items_data
        ]

        return cls(
            version=d.get('version', 1),
            source_paths=d.get('source_paths', []),
            report_metadata=meta,
            report_overrides=d.get('report_overrides', {}),
            report_plan_items=items,
        )
