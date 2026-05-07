# Rapportage-builders

Builders die uit `Project`, `Stage` en `AppState` herbruikbare rapport-fragmenten samenstellen: `ReportSection`-objecten met `TextBlock`s, `ReportField`s en `ReportTable`s. De builders zijn pure datatransformaties zonder Qt-afhankelijkheden en zonder state-mutatie.

## Bestanden

| Bestand | Doel |
|---|---|
| `input_description_builder.py` | Bouwt invoer-secties (fasekaarten, damwandkaart, beschrijvende `TextBlock`s) uit projectinvoer en bouwfases. |
| `result_description_builder.py` | Bouwt resultaat-secties met CUR 166-stappen (6.1 t/m 6.5) en bijbehorende `ReportField`s en `ReportTable`s uit rekenresultaten. |
| `soil_table_builder.py` | Levert per grondprofiel één `ReportSection` met de volledige grondparametertabel (BK/OK, gewichten, c', phi', delta, kh). |
| `damwand_hoofdstuk_builder.py` | Stelt het volledige damwand-hoofdstuk samen door damwandgegevens, grondprofielen en invoerbeschrijvingen te combineren. |

## Patroon

- **Input**: een `Project`, optioneel een `Stage`, plus instellingen uit `AppState`.
- **Output**: `ReportSection`-objecten (met `TextBlock`/`ReportField`/`ReportTable`/`ReportImageRequest`).
- **Geen Qt-imports**: builders zijn zuivere transformaties en kunnen headless draaien.
- **Geen state-mutatie**: builders lezen alleen uit het domeinmodel; tekstoverrides leven in `ReportState.overrides` en worden door `TextBlock.effective_text` toegepast.
- **Hulpfuncties lokaal**: elke builder definieert zijn eigen `_find()`-helper en gebruikt `fmt_number()` uit `utils.formatting` voor Nederlandse getalnotatie.

## Nieuwe builder toevoegen

1. Maak `reporting/builders/<naam>_builder.py` met `from __future__ import annotations` en imports uit `parsers.models` en `reporting.models`.
2. Definieer een klasse `<Naam>Builder` met een publieke `build(project, ...)`-methode die een `ReportSection` of `list[ReportSection]` teruggeeft.
3. Vul de sectie met `ReportField`, `ReportTable` of `TextBlock`; gebruik unieke `id`s zodat overrides en exporters de blokken kunnen herkennen.
4. Roep de builder aan vanuit `ReportController` of een hoger niveau zoals `DamwandHoofdstukBuilder`.
5. Mocht Word-export nodig zijn, registreer dan de blok-`id`s in de relevante exporter onder `exporters/`.
