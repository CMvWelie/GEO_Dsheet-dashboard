# Design: Grondsoortentabel als exporteerbaar selectie-item

**Datum:** 2026-04-14
**Status:** Goedgekeurd

## Samenvatting

De grondsoortentabel (momenteel alleen zichtbaar in de Grondsoorten-tab) wordt toegevoegd als selecteerbaar item in de Selectie-tab en opgenomen in de Excel- en Word-export. Elk grondprofiel krijgt een eigen selecteerbaar item. Dit wordt gerealiseerd via een generiek `extra_sections`-veld in `ReportPackage`, zodat toekomstige typen (afbeeldingen, verificatietabellen) hetzelfde pad volgen zonder modelwijzigingen.

---

## 1. Datamodel — `reporting/models.py`

`ReportPackage` krijgt één nieuw veld:

```python
extra_sections: list[ReportSection] = field(default_factory=list)
```

Alle bestaande velden blijven ongewijzigd. Bestaande code breekt niet.

`ReportPlan.build_package()` in `reporting/selection.py` krijgt een extra parameter:

```python
def build_package(
    self,
    metadata: ReportMetadata,
    input_sections: list[ReportSection],
    result_sections: list[ReportSection],
    extra_sections: list[ReportSection] | None = None,
) -> ReportPackage:
```

De `extra_sections` worden doorgezet naar `ReportPackage.extra_sections`.

---

## 2. Builder — `reporting/builders/soil_table_builder.py`

Nieuwe klasse `SoilTableBuilder` met methode:

```python
def build(self, project: Project) -> list[ReportSection]
```

- Retourneert één `ReportSection` per profiel in `project.profiles`
- **Sectie-id:** `soil_table_{profiel.name}` (lowercase, spaties → `_`)
- **Sectie-titel:** `Grondsoortentabel — {profiel.name}`
- Elke sectie bevat één `ReportTable` met 11 kolommen:

| Kolomnaam         | Bron                    |
|-------------------|-------------------------|
| `BK laag [m NAP]` | `layer.level`           |
| `OK laag [m NAP]` | `profiles.layers[i+1].level`, laatste laag → `'-'` |
| `Laag`            | `layer.material`        |
| `γd [kN/m³]`      | `soil.gamma_dry`        |
| `γn [kN/m³]`      | `soil.gamma_wet`        |
| `c'kar [kN/m²]`   | `soil.cohesion`         |
| `φ'kar [°]`       | `soil.phi`              |
| `δ [°]`           | `soil.delta`            |
| `kh1`             | `soil.kh1`              |
| `kh2`             | `soil.kh2`              |
| `kh3`             | `soil.kh3`              |

- Soil-parameters opzoeken via `{s.name: s for s in project.soils}`
- Ontbrekende soil (naam niet gevonden) → `'-'` in alle parameterkolommen
- Geen Qt-imports; `from __future__ import annotations` bovenaan conform coderingsconventie

---

## 3. Controller — `app/report_controller.py`

### 3a. Nieuwe methode

```python
def build_soil_sections(self) -> list[ReportSection]:
    project = self._app.get_active_project()
    if not project:
        return []
    return SoilTableBuilder().build(project)
```

### 3b. `auto_populate_plan()` uitbreiden

Na de bestaande invoer- en resultaatloops:

```python
for sec in self.build_soil_sections():
    self._report.plan.add_item(ReportItem(
        id=f'grondsoorten_{sec.id}',
        kind='grondsoorten',
        caption=sec.title,
        source_ref=sec.id,
    ))
```

`add_item` controleert al op duplicaten (op `id`), dus herhaald aanroepen is veilig.

### 3c. `build_package()` uitbreiden

```python
soil_secs = self.build_soil_sections()
pkg = self._report.plan.build_package(
    self._report.metadata, input_secs, result_secs,
    extra_sections=soil_secs,
)
```

---

## 4. Exporters

### Gemeenschappelijk patroon (beide exporters)

**Geselecteerde ids samenstellen** — de bestaande dubbele `input_`/`result_`-constructie wordt opgeschoond naar één uniforme lookup op `source_ref`, ongeacht `kind`:

```python
selected_ids = {i.source_ref for i in package.selected_items if i.source_ref}
```

**Alle secties samenvoegen:**

```python
all_sections = (
    package.input_sections
    + package.result_sections
    + package.extra_sections
)
```

**Filtercheck per sectie:**

```python
if selected_ids and sec.id not in selected_ids:
    continue
```

### Mapping-pad (`_write_with_mapping`)

`extra_sections` wordt toegevoegd aan `all_sections` ook in het mapping-pad, zodat grondsoorten straks via sidecar-mapping naar een benoemd werkblad/kop gestuurd kunnen worden.

---

## 5. UI — Selectie-tab

Geen wijzigingen aan `TabReportSelect`. Items verschijnen automatisch als:

```
[grondsoorten] Grondsoortentabel — Links
[grondsoorten] Grondsoortentabel — Rechts
```

Herordenen en verwijderen werkt via de bestaande knoppen.

`auto_populate_plan` wordt aangeroepen na bestandsverwerking — op dat moment zijn alle profielen beschikbaar.

---

## Toekomstige uitbreidingen

Nieuwe sectietypen (afbeeldingen, verificatietabellen, bijlagen) volgen hetzelfde pad:
1. Builder produceert `ReportSection`-objecten
2. Builder-resultaat gaat in `extra_sections` via `build_package`
3. `auto_populate_plan` voegt items toe met een nieuw `kind`
4. Exporters herkennen het nieuwe `kind` in `selected_ids`-opbouw
5. Speciale renderlogica (bv. PNG embedden) per `kind` in de exporters

Geen modelwijzigingen nodig voor `ReportPackage`.
