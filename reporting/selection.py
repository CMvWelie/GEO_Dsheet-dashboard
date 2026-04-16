"""ReportPlan — selectie, volgorde en exportdoel van rapportage-items."""

from __future__ import annotations

from reporting.models import ReportItem, ReportPackage, ReportMetadata, ReportSection


class ReportPlan:
    """Beheert de geselecteerde items, volgorde en exportdoelen voor een rapport."""

    def __init__(self) -> None:
        self.items: list[ReportItem] = []

    # ------------------------------------------------------------------
    # Mutaties
    # ------------------------------------------------------------------

    def add_item(self, item: ReportItem) -> None:
        """Voeg een item toe of werk source_ref bij als het al bestaat (op id)."""
        bestaand = next((i for i in self.items if i.id == item.id), None)
        if bestaand is None:
            item.order = len(self.items)
            self.items.append(item)
        elif item.source_ref and not bestaand.source_ref:
            # Zet source_ref alsnog bij bestaande items zonder ref (migratie)
            bestaand.source_ref = item.source_ref

    def reorder(self, item_id: str, new_order: int) -> None:
        """Verplaats item naar nieuwe positie (0-gebaseerd)."""
        item = next((i for i in self.items if i.id == item_id), None)
        if not item:
            return
        self.items.remove(item)
        new_order = max(0, min(new_order, len(self.items)))
        self.items.insert(new_order, item)
        self._renumber()

    def set_destination(self, item_id: str, excel: bool, word: bool) -> None:
        """Stel exportdoel in voor een item."""
        item = next((i for i in self.items if i.id == item_id), None)
        if item:
            item.included_excel = excel
            item.included_word = word

    # ------------------------------------------------------------------
    # Pakketbouw
    # ------------------------------------------------------------------

    def build_package(
        self,
        metadata: ReportMetadata,
        input_sections: list[ReportSection],
        result_sections: list[ReportSection],
        extra_sections: list[ReportSection] | None = None,
    ) -> ReportPackage:
        """Bouw een ReportPackage op basis van huidige plan en secties."""
        return ReportPackage(
            metadata=metadata,
            input_sections=input_sections,
            result_sections=result_sections,
            selected_items=list(self.items),
            extra_sections=extra_sections or [],
        )

    # ------------------------------------------------------------------
    # Hulp
    # ------------------------------------------------------------------

    def _renumber(self) -> None:
        for i, item in enumerate(self.items):
            item.order = i
