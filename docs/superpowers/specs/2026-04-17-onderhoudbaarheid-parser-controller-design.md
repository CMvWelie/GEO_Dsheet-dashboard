# Spec: Onderhoudbaarheid — shi_parser splitsen & AppController opsplitsen

**Datum:** 2026-04-17  
**Status:** Goedgekeurd, gereed voor implementatie

---

## Doel

`shi_parser.py` (1234 regels) is te groot voor één bestand en intimiderend als leerbron bij een nieuw formaat. `AppController` (325 regels) heeft te veel verantwoordelijkheden. Beide worden opgesplitst zonder de publieke interfaces te wijzigen.

---

## Architectuur

```
parsers/
├── shi/
│   ├── __init__.py      ← exporteert parse_project()
│   ├── coordinator.py   ← parse_project() als orkestrator
│   ├── geometry.py      ← profielen, maaiveld, waterstand
│   ├── stages.py        ← bouwfasen, belastingen
│   ├── soils.py         ← grondlagen, grondsoorten
│   ├── anchors.py       ← ankers, stutten
│   └── output.py        ← rekenresultaten (.shd/.shs)
├── shi_parser.py        ← deprecated stub: from parsers.shi import parse_project
└── __init__.py          ← registry ongewijzigd

app/
├── services/
│   ├── __init__.py
│   ├── ingest_service.py   ← bestand inlezen → raw_files
│   ├── parsing_service.py  ← FileBundle → Project (via parser-registry)
│   └── export_service.py   ← PNG, Word, Excel export
├── controller.py           ← dunne façade, delegeert naar services
└── viewport_service.py     ← ongewijzigd
```

---

## Componenten

### `parsers/shi/coordinator.py`

Bevat `parse_project(bundle: FileBundle) -> Project`. Roept functies aan uit de andere shi-modules. Geen parsing-logica zelf.

### `parsers/shi/geometry.py`

Alles rondom damwand-geometrie: profielen, maaiveld, waterstand, secties.

### `parsers/shi/stages.py`

Bouwfasen, belastingen, fasespecifieke instellingen.

### `parsers/shi/soils.py`

Grondlagen, grondsoorten, materiaaleigenschappen.

### `parsers/shi/anchors.py`

Ankers, stutten, verankering.

### `parsers/shi/output.py`

Rekenresultaten uit `.shd` en `.shs` bestanden.

### `parsers/shi/__init__.py`

```python
from parsers.shi.coordinator import parse_project

__all__ = ['parse_project']
```

### `parsers/shi_parser.py` (stub)

```python
# Deprecated: gebruik parsers.shi.parse_project
from parsers.shi import parse_project  # noqa: F401
```

### `app/services/ingest_service.py`

```python
class IngestService:
    def ingest_paths(self, paths: list[Path], state: AppState) -> tuple[bool, str]: ...
    def group_by_base_name(self, raw_files: dict[str, str]) -> dict[str, FileBundle]: ...
```

### `app/services/parsing_service.py`

```python
class ParsingService:
    def parse_bundle(self, bundle: FileBundle) -> tuple[Project | None, str]: ...
    def parse_all(self, bundles: dict[str, FileBundle]) -> dict[str, Project]: ...
```

Bij parsing-fouten: mislukte bundles worden overgeslagen, rest verwerkt.

### `app/services/export_service.py`

```python
class ExportService:
    def export_png(self, fig, path: Path) -> tuple[bool, str]: ...
    def export_word(self, package: ReportPackage, path: Path) -> tuple[bool, str]: ...
    def export_excel(self, package: ReportPackage, path: Path) -> tuple[bool, str]: ...
```

Gebruikt `get_exporter()` uit exporter-registry (zie spec uitbreidbaarheid).

### `app/controller.py` (dunne façade)

```python
class AppController:
    def __init__(self, state: AppState) -> None:
        self._state = state
        self._ingest = IngestService()
        self._parsing = ParsingService()
        self._export = ExportService()
        self._viewport = ViewportService()

    def ingest_paths(self, paths):
        return self._ingest.ingest_paths(paths, self._state)

    def process_files(self):
        bundles = self._ingest.group_by_base_name(self._state.raw_files)
        self._state.projects = self._parsing.parse_all(bundles)
```

Alle bestaande publieke methoden blijven bestaan. `main_window` merkt niets.

---

## Data flow

```
Bestand-ingest
  → AppController.ingest_paths()
  → IngestService.ingest_paths() → state.raw_files

Verwerking
  → AppController.process_files()
  → IngestService.group_by_base_name() → bundles
  → ParsingService.parse_all(bundles) → state.projects

Export
  → AppController.export_word()
  → ExportService.export_word() → get_exporter('word').export()
```

---

## Foutafhandeling

- Elke service-methode retourneert `tuple[bool, str]`
- `AppController` stuurt resultaat ongewijzigd door naar `main_window`
- Mislukte parse-bundles worden overgeslagen; succesvolle bundles worden verwerkt
- Geen exceptions buiten service-grenzen

---

## Testen

| Testbestand | Wat wordt getest |
|---|---|
| `tests/test_ingest_service.py` | Pad-groepering, ontbrekende bestanden, dubbele namen |
| `tests/test_parsing_service.py` | parse_bundle met geldige/ongeldige input |
| `tests/test_export_service.py` | Export-aanroepen met mock-exporter |
| `tests/test_shi_geometry.py` | Geometrie-functies geïsoleerd |
| `tests/test_shi_stages.py` | Fase-parsing geïsoleerd |
| `tests/test_parsers.py` | Ongewijzigd — blijft als integratietest |

---

## Scope & grenzen

**Binnen scope:**
- `shi_parser.py` opsplitsen in `parsers/shi/` subpakket
- `AppController` opsplitsen in drie services + dunne façade
- Stub `shi_parser.py` voor backwards-compatibiliteit

**Buiten scope:**
- Wijzigingen aan parsing-logica zelf
- Nieuwe bestandsformaten
- UI-aanpassingen
- `ReportController` (apart domein)
