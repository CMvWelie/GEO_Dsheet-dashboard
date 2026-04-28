# Ontwerp: Samenvattingstabel resultaten in Resultaatbeschrijving-tab

**Datum:** 2026-04-28  
**Status:** Goedgekeurd

## Doel

Voeg een samenvattingstabel toe onderaan het tabblad "Resultaatbeschrijving" die per fase en per CUR 166-verificatiestap de maatgevende momenten, dwarskrachten en vervormingen toont.

## Tabelstructuur

```
                 Momenten (kNm)                  Dwarskrachten (kN)              Vervormingen (mm)
Fase    6.1  6.2  6.3  6.4  6.5  6.5×factor    6.1  6.2  6.3  6.4  6.5  6.5×factor    6.1  6.2  6.3  6.4  6.5  6.5×factor
Fase 1  ...  ...  ...  ...  ...  ...           ...  ...  ...  ...  ...  ...           ...  ...  ...  ...  ...  ...
Fase 2  ...  ...  ...  ...  ...  ...           ...  ...  ...  ...  ...  ...           ...  ...  ...  ...  ...  ...
```

- Datarijen: één per constructiefase.
- Waarden: max(abs(max), abs(min)) per attribuut (moment, shear, disp) over alle punten in de betreffende ResultStage.
- Stappen worden dynamisch bepaald uit `project.result_steps.keys()`, gesorteerd.
- Ontbrekende combinaties (fase/stap niet aanwezig): "-".

## Wijzigingen

### 1. `reporting/builders/result_description_builder.py`

**`_step_short_label()`** — volledig label voor de factor-stap:

```python
return m.group(1).replace(' x factor', ' × factor')
# was: .replace(' x factor', ' × f')
```

**`_per_phase_summary()`** — kolomlabels en groepskoppen:

```python
# Kolomlabels: stap_labels herhaald per groep (geen M/V/u prefix meer)
kolommen = ['Fase'] + stap_labels + stap_labels + stap_labels

# Groepskoppen
column_groups=[
    ('', 1),
    ('Momenten (kNm)', n),
    ('Dwarskrachten (kN)', n),
    ('Vervormingen (mm)', n),
]
```

### 2. `ui/tabs/tab_result_desc.py`

**`_maak_styled_tabel()`** — 2-rij koptabel wanneer `column_groups` gevuld is:

- Als `table.column_groups` niet leeg is:
  - **Grid-rij 0**: groepkoppen, elk gespannen over hun `colspan` via `grid.addWidget(lbl, 0, col_offset, 1, colspan)`. Stijl: achtergrond `#274f77`, witte tekst, gecentreerd.
  - Lege groep (colspan 1, boven "Fase"): zelfde donkere achtergrond `#1b3a5c` als de kolomkop eronder.
  - **Grid-rij 1**: kolomkoppen — ongewijzigde stijl (`#1b3a5c`).
  - **Grid-rij 2+**: datarijen.
- Als `table.column_groups` leeg is: gedrag ongewijzigd (rij 0 = kolomkoppen, rij 1+ = data) — geen regressie voor andere tabellen.

## Wat niet verandert

- Plaatsing: de tabel staat al onderaan de Resultaatbeschrijving-tab als laatste sectie ("Maximale resultaten per fase" QGroupBox). Geen wijziging in volgorde of `main_window.py`.
- `separator_before_cols`: veld blijft bestaan in `ReportTable` maar wordt niet gerenderd in de tab-widget — groepkoppen bieden al visuele scheiding.
- Eenheden in de data: `fmt_number()` ongewijzigd; waarden zijn max abs-waarden direct uit `ResultPoint`.

## Randgevallen

- Geen resultaatdata (`result_steps` leeg): bestaande "-" fallback in `_per_phase_summary` werkt ongewijzigd.
- Slechts één stap beschikbaar: tabel toont die ene stap per groep.
- Groep met colspan 0: kan niet voorkomen (stap_keys altijd ≥ 1 als result_steps gevuld is).
