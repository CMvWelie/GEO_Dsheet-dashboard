# Rapportage

Domeinmodellen en selectielogica voor de rapportagelaag. Deze map bevat de
dataklassen voor rapportinhoud en het `ReportPlan` dat items verzamelt; de
concrete opbouw uit parserdata gebeurt in submap `builders/`.

## Bestanden

| Bestand | Doel |
|---|---|
| `models.py` | Dataclasses voor velden, tabellen, tekstblokken, secties en het volledige rapportpakket. |
| `selection.py` | `ReportPlan`-klasse die selectie, volgorde en exportdoelen per item beheert. |
| `figure_renderer.py` | `render_figuur()` — headless rendering van een `ReportImageRequest` naar PNG-bytes voor rapportage-export; geen Qt. |

## Modellen

Gedefinieerd in `models.py`:

- `ReportField` — losse sleutel-waardepaar met label en optionele eenheid.
- `ReportTable` — tabel met kolomkoppen, rijen, optionele kolomgroepen en
  scheidingslijnen; `inline=True` voor inline weergave.
- `TextBlock` — tekstuele beschrijving met `generated_text` en optionele
  `manual_override`; via `effective_text` wordt automatisch de override of de
  gegenereerde tekst geretourneerd.
- `ReportSection` — bundelt `ReportField`s, `ReportTable`s, `TextBlock`s en
  `ReportImageRequest`s onder één titel.
- `ReportPackage` — eindcontainer met `ReportMetadata`, invoer-, resultaat- en
  extra-secties, geselecteerde items en een optioneel Word-templatepad.

Aanvullend: `ReportImageRequest` (figuurverzoek per fase/stap), `ReportItem`
(selecteerbaar item met volgorde en exportvlaggen) en `ReportMetadata`
(projectgegevens, auteur, logo, profiel).

## Pijplijn

```
Builder  ->  ReportSection  ->  WordHoofdstukExporter
```

De builders in `builders/` lezen `Project`/`Stage` uit en produceren
`ReportSection`s. `ReportController` selecteert de gewenste secties uit het plan
en geeft die rechtstreeks door aan `WordHoofdstukExporter`.

## TextBlock-overrides

Handmatig aangepaste teksten worden bewaard in `ReportState.overrides`, een
mapping van `block_id` naar de vervangtekst. Bij het opbouwen van een
`TextBlock` wordt een aanwezige override op `manual_override` gezet; de property
`effective_text` retourneert dan de override en valt anders terug op
`generated_text`. Hierdoor blijven gegenereerde basisteksten beschikbaar, ook
nadat de gebruiker een eigen tekst heeft ingevoerd.

## Submap

- `builders/` — concrete builders die parserdata omzetten naar
  `ReportSection`s (eigen README in die map).
