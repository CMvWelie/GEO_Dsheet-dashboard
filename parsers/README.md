# Parsers

Parsen van D-Sheet bestandsformaten (`.shi`, `.shd`, `.shs`) naar domein-dataclasses
in `models.py`. Een lichte plugin-registry koppelt extensies aan een parser-callable,
zodat extra formaten zonder aanpassing van de aanroeplogica toegevoegd kunnen worden.

## Bestanden

| Bestand | Doel |
|---|---|
| `__init__.py` | Plugin-registry (`register_parser`, `get_parser`) en registratie van de ingebouwde D-Sheet parser. |
| `models.py` | Dataclasses voor alle domeinobjecten (project, geometrie, belastingen, resultaten). |
| `base_parser.py` | Gedeelde regex-helpers `extract_section()` en `find_line_value()`. |
| `shi_parser.py` | Volledige D-Sheet parser; bouwt een `Project` uit een `FileBundle` met `.shi`/`.shd`/`.shs` tekst. |

## Domeinmodellen

Centraal staat `Project`, dat alle domeinlijsten bundelt. Per categorie:

- Geometrie: `SoilLayer`, `SoilProfile`, `Surface`, `WaterLevel`, `Soil`.
- Constructie: `SheetPilingElement`, `Anchor`, `Strut`, `SpringSupport`, `RigidSupport`.
- Belastingen: `UniformLoad`, `SurchargeLoad`, `HorizontalLineLoad`, `Moment`, `NormalForce`.
- Bouwfases: `Stage` (verwijst per fase naar profielen, oppervlakken, waterstanden en belastingen op naam).
- Resultaten: `ResultStep`, `ResultStage`, `ResultPoint`, `ResultSummary`,
  `AnchorStrutResumeItem`, `SupportResumeItem`.
- Bestandsbundel: `FileBundle` (ruwe tekst per extensie).

Alle modellen zijn `@dataclass` met `field(default_factory=list)` voor lijsten;
geen Qt-imports en geen ruwe dicts in publieke API's.

## Nieuwe parser toevoegen

Een nieuw formaat registreer je vanuit het pakket-init of een extra module:

```python
from parsers import register_parser
from parsers.models import FileBundle, Project

def parse_plaxis(file_bundle: FileBundle, base_name: str) -> Project:
    # Lees file_bundle.shi/.shd/.shs of voeg eigen velden toe via een wrapper.
    ...

register_parser('plx', parse_plaxis)
```

De callable krijgt `(file_bundle, base_name)` en moet een `Project` teruggeven.
`AppController` haalt de juiste parser op via `get_parser(extensie)`.

## Conventies

- Geen Qt-imports; parsers zijn puur datagericht en headless te draaien.
- Herstelbare fouten worden via lege strings of lege lijsten teruggegeven; harde
  parserfouten propageren als exception en worden bovenliggend afgevangen tot
  `tuple[bool, str]` in de controller.
- Domeinmodellen zijn `@dataclass`; muteerbare standaardwaarden via
  `field(default_factory=...)`.
- Sectie-extractie loopt altijd via `extract_section()` zodat `[SECTION]` /
  `[END OF SECTION]` consistent worden behandeld.
