# Parsers

Parsen van D-Sheet `.shd`-bestanden naar
domein-dataclasses in `models.py`.

## Bestanden

| Bestand | Doel |
|---|---|
| `__init__.py` | Pakketmarkering, geen re-exports. |
| `models.py` | Dataclasses voor alle domeinobjecten (project, geometrie, belastingen, resultaten). |
| `base_parser.py` | Gedeelde regex-helpers `extract_section()` en `find_line_value()`. |
| `shi_parser.py` | Volledige D-Sheet parser; historische modulenaam, bouwt een `Project` uit een `FileBundle` met `.shd`-tekst. |

## Domeinmodellen

Centraal staat `Project`, dat alle domeinlijsten bundelt. Per categorie:

- Geometrie: `SoilLayer`, `SoilProfile`, `Surface`, `WaterLevel`, `Soil`.
- Constructie: `SheetPilingElement`, `Anchor`, `Strut`, `SpringSupport`, `RigidSupport`.
- Belastingen: `UniformLoad`, `SurchargeLoad`, `HorizontalLineLoad`, `Moment`, `NormalForce`.
- Bouwfases: `Stage` (verwijst per fase naar profielen, oppervlakken, waterstanden en belastingen op naam).
- Resultaten: `ResultStep`, `ResultStage`, `ResultPoint`, `ResultSummary`,
  `AnchorStrutResumeItem`, `SupportResumeItem`.
- Bestandsbundel: `FileBundle` (ruwe `.shd`-tekst).

Alle modellen zijn `@dataclass` met `field(default_factory=list)` voor lijsten;
geen Qt-imports en geen ruwe dicts in publieke API's.

## Conventies

- Geen Qt-imports; parsers zijn puur datagericht en headless te draaien.
- Herstelbare fouten worden via lege strings of lege lijsten teruggegeven; harde
  parserfouten propageren als exception en worden bovenliggend afgevangen tot
  `tuple[bool, str]` in de controller.
- Domeinmodellen zijn `@dataclass`; muteerbare standaardwaarden via
  `field(default_factory=...)`.
- Sectie-extractie loopt altijd via `extract_section()` zodat `[SECTION]` /
  `[END OF SECTION]` consistent worden behandeld.
