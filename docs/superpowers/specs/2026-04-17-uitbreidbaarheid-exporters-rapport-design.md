# Spec: Uitbreidbaarheid — Exporter-registry & Rapport-registratie

**Datum:** 2026-04-17  
**Status:** Goedgekeurd, gereed voor implementatie

---

## Doel

Herstel de asymmetrie tussen parsers en exporters: parsers hebben een registry, exporters niet. Voeg ook een centrale registratie toe voor rapport-builders zodat nieuwe secties één bestand + één registratie kosten.

---

## Architectuur

```
exporters/
├── __init__.py          ← register_exporter(), get_exporter(), _registry
├── base_exporter.py     ← BaseExporter ABC
├── excel_exporter.py    ← ExcelExporter(BaseExporter)
├── word_exporter.py     ← WordExporter(BaseExporter)
└── word_hoofdstuk_exporter.py  ← WordHoofdstukExporter(BaseExporter)

reporting/
├── __init__.py          ← register_builder(), get_builders(), _registry
└── builders/
    ├── damwand_hoofdstuk_builder.py  ← @register_builder
    ├── input_description_builder.py  ← @register_builder
    ├── result_description_builder.py ← @register_builder
    └── soil_table_builder.py         ← @register_builder
```

---

## Componenten

### `exporters/base_exporter.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from reporting.models import ReportPackage

class BaseExporter(ABC):
    @abstractmethod
    def export(self, package: ReportPackage, path: Path) -> tuple[bool, str]: ...
```

### `exporters/__init__.py`

```python
_registry: dict[str, type[BaseExporter]] = {}

def register_exporter(fmt: str, cls: type[BaseExporter]) -> None:
    _registry[fmt] = cls

def get_exporter(fmt: str) -> BaseExporter:
    return _registry[fmt]()
```

Elke exporter registreert zichzelf onderaan zijn module bij import:
```python
# onderaan excel_exporter.py
register_exporter('excel', ExcelExporter)
```

Importeer exporters expliciet in `exporters/__init__.py` zodat registratie plaatsvindt bij app-start:
```python
from exporters import excel_exporter, word_exporter, word_hoofdstuk_exporter  # noqa: F401
```

### `reporting/__init__.py`

```python
_builder_registry: list[type] = []

def register_builder(cls: type) -> type:
    _builder_registry.append(cls)
    return cls  # bruikbaar als decorator

def get_builders() -> list[type]:
    return list(_builder_registry)
```

Builders registreren zichzelf via decorator:
```python
@register_builder
class DamwandHoofdstukBuilder: ...
```

`ReportController` itereert over `get_builders()` i.p.v. hardcoded instantiaties.

---

## Data flow

```
App-start
  → exporters/__init__.py importeert alle exporter-modules
  → elke module roept register_exporter() aan
  → reporting/__init__.py importeert alle builder-modules
  → elke module roept register_builder() aan (via decorator)

Exporteer-actie
  → ReportController.export_word(package, path)
  → get_exporter('word').export(package, path)
  → tuple[bool, str] terug naar controller → QMessageBox indien fout
```

---

## Foutafhandeling

- `get_exporter(fmt)` gooit `KeyError` bij onbekend formaat
- Controller vangt op: `(False, f"Onbekend exportformaat: {fmt}")`
- `BaseExporter.export()` retourneert `tuple[bool, str]` conform bestaand patroon
- Geen andere uitzonderingen op dit niveau

---

## Testen

| Testbestand | Wat wordt getest |
|---|---|
| `tests/test_exporter_registry.py` | Registreer dummy-exporter, verifieer `get_exporter()` retourneert juiste instantie; KeyError bij onbekend formaat |
| `tests/test_builder_registry.py` | Registreer dummy-builder, verifieer `get_builders()` bevat hem; volgorde bewaard |
| Bestaande exporter-tests | Gedrag ongewijzigd — alleen interface toegevoegd |

---

## Scope & grenzen

**Binnen scope:**
- `BaseExporter` ABC en registry
- Bestaande exporters implementeren `BaseExporter`
- `ReportController` gebruikt `get_exporter()` i.p.v. directe imports
- Builder-registry in `reporting/__init__.py`
- Builders registreren zichzelf via `@register_builder`

**Buiten scope:**
- Nieuwe exportformaten (PDF, CSV) — volgen daarna triviaal
- Wijzigingen aan `ReportPackage` of exporter-logica zelf
- UI-aanpassingen
