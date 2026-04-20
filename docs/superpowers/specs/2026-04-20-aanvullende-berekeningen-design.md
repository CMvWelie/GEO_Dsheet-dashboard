# Design: Aanvullende berekeningen tab

**Datum:** 2026-04-20
**Status:** Goedgekeurd

## Overzicht

Voeg een nieuwe hoofdtab "Aanvullende berekeningen" toe aan het D-Sheet Dashboard.
De tab bevat een interne `QTabWidget` waarvan het eerste subtabje "Hydraulische Grondbreuk"
de NEN 9997-1:2016-controle uitvoert. De subtabstructuur is uitbreidbaar voor toekomstige berekeningen.

## Architectuur

### Nieuwe bestanden

| Bestand | Doel |
|---|---|
| `ui/tabs/tab_aanvullende_berekeningen.py` | Container-widget met interne `QTabWidget`; delegeert `update_project()` naar actieve subtab |
| `ui/tabs/tab_hydraulische_grondbreuk.py` | Subtab-widget met invoervelden, auto-invul-logica en resultaatweergave |

### Wijzigingen in bestaande bestanden

| Bestand | Wijziging |
|---|---|
| `app/main_window.py` | Importeer en instantieer `TabAanvullendeBerekeningen`; voeg toe als tab vóór "Instellingen"; roep `update_project()` aan bij project-wissel |

## Data-koppeling

Auto-invul vanuit `Project` (bij `update_project(project: Project | None)`):

| Veld | Bron | Fallback |
|---|---|---|
| Inheiniveau damwand (m NAP) | `project.sheet_piling[0].bottom` | leeg / handmatig |
| Grondwaterstand buiten (m NAP) | `max(wl.level for wl in project.waterlevels)` | leeg / handmatig |
| Grondgewicht γ (kN/m³) | `project.soils[0].gamma_wet` | leeg / handmatig |
| Bouwputniveau (m NAP) | niet automatisch bepaalbaar | handmatig invullen |
| Materiaalfactor ψ (–) | vast 0,9 (NEN 9997-1:2016) | aanpasbaar |
| Watergewicht γ_w (kN/m³) | vast 10,0 | aanpasbaar |

Auto-ingevulde velden (inheiniveau, grondwaterstand, grondgewicht) krijgen een reset-knop (↺)
die de waarde terugzet naar de projectwaarde.

## Berekening (NEN 9997-1:2016)

```
dikte_grondwig  = bouwputniveau − inheiniveau          [m]
P_stab          = dikte_grondwig × γ × ψ               [kN/m²]
P_water         = (grondwaterstand − inheiniveau) × γ_w [kN/m²]
UC              = P_stab / P_water                      [–]
status          = "VOLDOET" als UC ≥ 1,0 anders "VOLDOET NIET"
```

Herberekening vindt direct plaats bij elke wijziging van een invoerveld.

## UI-layout (TabHydraulischeGrondbreuk)

```
┌─ Invoer ──────────────────────────────────────────────┐
│  Bouwputniveau (m NAP)           [  2.60 ]            │
│  Inheiniveau damwand (m NAP)     [ -1.00 ] ↺          │
│  Grondgewicht γ (kN/m³)          [ 19.00 ] ↺          │
│  Grondwaterstand buiten (m NAP)  [  8.00 ] ↺          │
│  Materiaalfactor ψ (–)           [  0.90 ]            │
│  Watergewicht γ_w (kN/m³)        [ 10.00 ]            │
└───────────────────────────────────────────────────────┘
┌─ Resultaat ───────────────────────────────────────────┐
│  Stabiliserende druk             61,56 kN/m²          │
│  Aandrijvende waterdruk          90,00 kN/m²          │
│  Gebruiksgraad (UC)              0,684                 │
│  ██ VOLDOET NIET ██   (rood banner / groen bij ≥ 1)   │
└───────────────────────────────────────────────────────┘
```

## Conventies

- Klasse `TabAanvullendeBerekeningen(QWidget)` in `tab_aanvullende_berekeningen.py`
- Klasse `TabHydraulischeGrondbreuk(QWidget)` in `tab_hydraulische_grondbreuk.py`
- Geen Qt-imports in controllers; berekening blijft puur in de widget
- Getallen geformatteerd via `fmt_number()` uit `utils/formatting.py`
- Stijl volgt bestaande kleurconstanten (`_HDR_BG`, `_ROW_ODD_BG`, etc.)

## Uitbreidbaarheid

`TabAanvullendeBerekeningen` roept `self._tabs.addTab(...)` aan voor elke subtab.
Toekomstige subtabs (bv. "Verticaal evenwicht", "Opdrijven") worden als afzonderlijke
`QWidget`-subklassen toegevoegd zonder wijzigingen aan de containerklasse.
