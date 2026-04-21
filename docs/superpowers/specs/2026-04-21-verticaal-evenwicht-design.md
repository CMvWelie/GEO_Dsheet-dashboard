# Ontwerp: TabVerticaalEvenwicht

**Datum:** 2026-04-21
**Status:** Goedgekeurd

## Samenvatting

Nieuw subtabblad "Verticaal evenwicht" onder de hoofdtab "Aanvullende berekeningen". Controleert de stabiliteit tegen opbarsten (hydraulische grondbreuk van onderaf) conform NEN 9997-1:2016 artikel 10.2(a). Zoveel mogelijk auto-invul vanuit het D-Sheet project, met reset-knopjes voor handmatige override.

---

## 1. Architectuur & moduleopbouw

**Nieuw bestand:** `ui/tabs/tab_verticaal_evenwicht.py`

Bevat uitsluitend:

| Onderdeel | Type | Doel |
|---|---|---|
| `TaludGeometrie` | `@dataclass` | `(maaiveld_niveau: float, helling_h_per_v: float)` |
| `AutoWaardenVE` | `@dataclass` | Alle auto-ingevulde waarden vanuit Project |
| `extraheer_auto_waarden_ve(project, stage_naam, profiel_zijde)` | pure functie | Extraheert waarden uit Project; geen Qt |
| `bereken_verticaal_evenwicht(...)` | pure functie | Hoofdberekening; geeft `(Gstb_d, Vdst_d, UC)` terug |
| `bereken_taludinvloed(d1, a, b, d2)` | pure functie | f-factor formule NEN 9997-1 |
| `TabVerticaalEvenwicht(QWidget)` | klasse | Het tabwidget |

**Aanpassing:** `tab_aanvullende_berekeningen.py` — importeert `TabVerticaalEvenwicht` en voegt toe als tweede subtab.

### AutoWaardenVE dataclass

```python
@dataclass
class AutoWaardenVE:
    ontgravingsniveau: float | None        # laagste y van Surface-bodempunten
    breedte_bouwputbodem: float | None     # |x_rechts - x_links| van bodempunten
    stijghoogte: float | None              # max WaterLevel.level
    waterpeil_bouwput: float | None        # max WaterLevel.level (zelfde bron, aparte spin)
    grondlagen: list[tuple[str, float, float, float, float]]  # (naam, b.k., o.k., γdr, γnat)
    talud_links: TaludGeometrie | None
    talud_rechts: TaludGeometrie | None
```

---

## 2. Data-extractie uit D-Sheet

| Veld | Bron in Project |
|---|---|
| Ontgravingsniveau | Laagste y-coördinaat van de twee bodempunten (laagste y) van de gekozen Surface |
| Breedte bouwputbodem | \|x_rechts − x_links\| van diezelfde twee bodempunten |
| Stijghoogte w.v.p. | `max(wl.level for wl in project.waterlevels)` |
| Waterpeil in bouwput | `max(wl.level for wl in project.waterlevels)` (zelfde bron, apart aanpasbaar) |
| Grondlagen | `SoilProfile.layers` (niveaus) + `Soil.gamma_dry` / `Soil.gamma_wet` via materiaalnaam |
| Taludgeometrie links | `Stage.left_surface` → `Surface.points` |
| Taludgeometrie rechts | `Stage.right_surface` → `Surface.points` |

**Stage-keuze:** gebruiker kiest via dropdown bovenaan de tab. Bij wisseling worden auto-waarden opnieuw ingeladen; handmatige overrides blijven behouden zolang `project.base_name` niet wijzigt.

**Profiel-keuze:** tweede dropdown — links of rechts profiel (`Stage.left_profile` / `Stage.right_profile`) als basis voor de grondlagen.

**Taludgeometrie afleiden:**
- Helling = Δy/Δx over het schuine deel van de Surface-punten (niet-horizontale segmenten)
- Maaiveld_niveau = hoogste y-waarde van de Surface
- Vlak terrein (alle y gelijk): helling = 0, taludinvloed-checkbox uitgeschakeld

---

## 3. Berekeningslogica

### Hoofdberekening (opbarsten)

```
Gstb;d = (Σ dikte_boven_wp × γ_dr;rep + Σ dikte_onder_wp × γ_nat;rep) × materiaalfactor

Vdst;d = (stijghoogte − evenwichtsniveau) × γ_w

UC = Gstb;d / Vdst;d   (≥ 1.0 = voldoet)
```

- `wp` = waterpeil in bouwput
- Lagen van `ontgravingsniveau` tot `evenwichtsniveau`
- `evenwichtsniveau` = o.k. van de door de gebruiker gekozen laag (dropdown)

### Taludinvloed (beide zijden afzonderlijk)

```
d1 = maaiveld_niveau − ontgravingsniveau
a  = d1 × helling_h_per_v
b  = breedte_bouwputbodem / 2
d2 = ontgravingsniveau − evenwichtsniveau

f = (2/π) × [(1 + b/a) × arctan(d2/(a+b)) − (b/a) × arctan(d2/b)]

gewicht_talud = Σ(dikte_laag_in_talud × γ_dr;rep)   (grond boven ontgravingsniveau)
bijdrage      = f × gewicht_talud
```

De **laagste bijdrage** van links en rechts wordt opgeteld bij Gstb;d.
UC_met_talud = (Gstb;d + min(bijdrage_links, bijdrage_rechts)) / Vdst;d

---

## 4. UI-layout

### Blok 1 — Projectinstellingen (QGroupBox)

| Element | Type |
|---|---|
| Stage-keuze | `QComboBox` |
| Grondprofiel (links/rechts) | `QComboBox` |
| Evenwichtsniveau-laag | `QComboBox` (gevuld vanuit grondprofiel) |

### Blok 2 — Invoer (QGroupBox, grid: label | spinbox | reset-knop)

| Veld | Eenheid | Auto? | Reset? |
|---|---|---|---|
| Ontgravingsniveau | m NAP | ✓ | ✓ |
| Waterpeil in bouwput | m NAP | ✓ | ✓ |
| Stijghoogte w.v.p. | m NAP | ✓ | ✓ |
| Materiaalfactor γG;stb | − | standaard 0.9 | — |
| Watergewicht γ_w | kN/m³ | standaard 10.0 | — |
| [checkbox] Taludinvloed meenemen | | | |
| → Breedte bouwputbodem | m | ✓ | ✓ |
| → Helling links (v:h) | tekst "1:3" | ✓ | ✓ |
| → Helling rechts (v:h) | tekst "1:3" | ✓ | ✓ |

Taludinvloed-velden conditioneel zichtbaar via checkbox.

### Blok 3 — Resultaat (QGroupBox)

| Label | Inhoud |
|---|---|
| Gstb;d | waarde in kN/m² |
| Vdst;d | waarde in kN/m² |
| UC zonder taludinvloed | getal |
| UC met taludinvloed | getal (alleen zichtbaar als checkbox aan) |
| Statusbalk | VOLDOET (groen) / VOLDOET NIET (rood) / GEEN WATERDRUK (grijs) |

Statusbalk toont UC mét talud als checkbox aan, anders UC zonder talud.

---

## 5. Foutafhandeling & randgevallen

| Situatie | Gedrag |
|---|---|
| Geen project geladen | Spinboxes disabled, resultaat '–' |
| Evenwichtsniveau-dropdown leeg | UC niet berekend, statusbalk neutraal |
| Vdst;d = 0 | UC = ∞, statusbalk grijs "GEEN WATERDRUK" |
| Vlak terrein (helling = 0) | Taludinvloed-checkbox uitgeschakeld |
| a = 0 (ontgravingsniveau = maaiveld) | Taludinvloed niet berekend |
| Stage-wissel | Handmatige overrides behouden zolang `base_name` gelijk is |

---

## 6. Relatie tot bestaande code

- Volgt exact hetzelfde patroon als `TabHydraulischeGrondbreuk`
- Geen Qt-imports buiten `tab_verticaal_evenwicht.py`
- `tab_aanvullende_berekeningen.py`: `update_project()` propageert naar beide subtabs
- Nieuwe subtab toegevoegd als tweede tab na "Hydraulische Grondbreuk"
