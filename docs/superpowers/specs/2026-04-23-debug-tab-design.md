# Debug-tab — Ontwerpdocument

**Datum:** 2026-04-23
**Status:** Goedgekeurd

---

## Doel

Een "Debug"-tab toevoegen tussen "Rapportcontext" en "Doorsnede" die alle momenteel geparste projectdata in tabelform toont. Bedoeld om te controleren of de parser data correct uitleest en om hiaten in de parsing te identificeren.

---

## Structuur & bestanden

### Nieuwe bestanden

| Bestand | Inhoud |
|---|---|
| `ui/tabs/tab_debug.py` | Container-tab; QWidget met QTabWidget (patroon = `TabAanvullendeBerekeningen`) |
| `ui/tabs/tab_debug_invoer.py` | "Invoer"-subtab |
| `ui/tabs/tab_debug_uitvoer.py` | "Uitvoer"-subtab |

### Aanpassingen bestaande bestanden

| Bestand | Wijziging |
|---|---|
| `app/main_window.py` | Import + `insertTab(1, self._tab_debug, 'Debug')` tussen Rapportcontext en Doorsnede |
| `app/main_window.py` | `self._tab_debug.update_project(project)` aanroepen vanuit `_update_all()` |

### Publieke API

```python
class TabDebug(QWidget):
    def update_project(self, project: Project | None) -> None: ...

class TabDebugInvoer(QWidget):
    def update_project(self, project: Project | None) -> None: ...

class TabDebugUitvoer(QWidget):
    def update_project(self, project: Project | None) -> None: ...
```

---

## Technische aanpak

**Widget-structuur per subtab:**
- `QScrollArea` (widgetResizable=True) met een `QWidget` + `QVBoxLayout`
- Sectieheaders: vetgedrukte `QLabel` als visuele scheidslijn
- Data: `QTableWidget` per sectie (kopieerbaar via context-menu, native Qt)
- Collapsible secties (alleen uitvoer): `QPushButton` met `▶`/`▼`-prefix + `QTableWidget` die zichtbaar/onzichtbaar toggled

**Update-patroon:** automatisch verversen bij projectwisseling via `_update_all()`.

**Weggelaten velden:**
- `file_bundle` — ruwe bestandstekst, te groot
- `soil_color_map` — afgeleid woordenboek, al zichtbaar via GRONDSOORTEN

---

## "Invoer"-subtab — secties (van boven naar beneden)

Één doorscrolbare lijst; sectieheader + QTableWidget per categorie.

### 1. PROJECT
| veld | waarde |
|---|---|
| base_name | ... |
| project_name | ... |

### 2. DAMWANDELEMENTEN
Kolommen: name · x · bottom · top · width · height_mm · pile_width_mm · EI [kNm²/m] · A [cm²/m] · Wres [cm³/m] · Mkar [kNm/m] · Mopn [kNm/m] · staalsoort

### 3. WATERPEILEN
Kolommen: name · level [m NAP]

### 4. GRONDSOORTEN
Kolommen: name · kleur · γd · γn · c' · φ · δ · kh1 · kh2 · kh3

### 5. GRONDPROFIELEN
Per profiel: sectieheader met profielnaam, dan tabel met kolommen: nr · level · wosp_top · wosp_bottom · material

### 6. MAAIVELDLIJNEN
Per oppervlak: sectieheader met naam, dan tabel: nr · x · y

### 7. ANKERS
Kolommen: nr · name · level · E-mod · doorsnede · lengte · vloeigrens · hoek · hoogte · zijde

### 8. STEMPELS
Kolommen: nr · name · level · E-mod · doorsnede · lengte · vloeigrens · hoek · aux · zijde

### 9. VERINGSSTEUNEN
Kolommen: nr · name · level · rot_stiff · tr_stiff

### 10. STIJVE STEUNEN
Kolommen: nr · name · level · rot_stiff · tr_stiff

### 11. GELIJKMATIGE BELASTINGEN
Kolommen: name · links · rechts · permanent · gunstig

### 12. LIJNBELASTINGEN
Kolommen: nr · name · level · waarde · permanent · gunstig

### 13. MAAIVELDBELASTINGEN
Per belasting: sectieheader met naam, dan tabel: afstand · waarde

### 14. MOMENTEN
Kolommen: nr · name · level · waarde · permanent · gunstig

### 15. NORMAALKRACHTEN
Kolommen: nr · name · top · vlak_links · vlak_rechts · bottom · permanent · gunstig

### 16. FASE [naam] — één blok per fase
Eerst een key-value tabel:
| veld | waarde |
|---|---|
| method_line | ... |
| left_surface | ... |
| right_surface | ... |
| left_water | ... |
| right_water | ... |
| left_profile | ... |
| right_profile | ... |

Dan per aanwezige lijst een sub-tabel met de **volledig opgeloste objectdata**:
- **Ankers**: zelfde kolommen als sectie 7
- **Stempels**: zelfde kolommen als sectie 8
- **Veringssteunen**: zelfde kolommen als sectie 9
- **Stijve steunen**: zelfde kolommen als sectie 10
- **Gelijkmatige belastingen**: zelfde kolommen als sectie 11
- **Lijnbelastingen**: zelfde kolommen als sectie 12
- **Maaiveldbelastingen links** (uit `stage.surcharge_loads_left`): zelfde kolommen als sectie 13
- **Maaiveldbelastingen rechts** (uit `stage.surcharge_loads_right`): zelfde kolommen als sectie 13
- **Momenten**: zelfde kolommen als sectie 14
- **Normaalkrachten**: zelfde kolommen als sectie 15

---

## "Uitvoer"-subtab — secties

### 1. RESULTAATSAMENVATTING (niet collapsible)
Kolommen: fase · max moment [kNm/m] · max dwarskracht [kN/m] · max verplaatsing [mm] · mob. moment [%] · mob. grond [%]

### 2. ONDERSTEUNINGSKRACHTEN (niet collapsible)
Kolommen: fase · naam · kracht [kN/m] · niveau [m NAP]
Bron: `ResultSummary.ondersteuningen`

### 3. ANKER/STEMPEL RESUMÉ (niet collapsible)
Kolommen: fase · naam · verificatietype · basis_cur_step · partial_factor_set · repr. factor · kracht · ankertype · ankerstatus · gewijzigd naar vloeiend · rekenstatus

### 4. STEUNEN RESUMÉ (niet collapsible)
Kolommen: fase · naam · verificatietype · basis_cur_step · partial_factor_set · repr. factor · kracht · moment · steuntype · rekenstatus

### 5+. GRAFIEKPUNTEN — [rekenstap] (collapsible, standaard ingeklapt)
Één blok per `ResultStep` (sleutel = genormaliseerd stap-label).
Header: `▶ GRAFIEKPUNTEN — [rekenstap]` → klikken toont/verbergt tabel.
Kolommen: fase · diepte [m NAP] · moment [kNm/m] · dwarskracht [kN/m] · verplaatsing [mm]
Rijen: alle `ResultPoint`-objecten van alle fasen binnen die stap, gegroepeerd per fase.

---

## Opzoeklogica voor fase-objecten

`Stage` slaat alleen namen op als verwijzingen (bv. `stage.anchors = ['Anker-A']`). Bij het renderen van een fase worden de namen opgezocht in de bijbehorende projectlijsten:

```
stage.anchors          → opzoeken in project.anchors          (op .name)
stage.struts           → opzoeken in project.struts           (op .name)
stage.spring_supports  → opzoeken in project.spring_supports  (op .name)
stage.rigid_supports   → opzoeken in project.rigid_supports   (op .name)
stage.uniform_loads    → opzoeken in project.uniform_loads    (op .name)
stage.horizontal_line_loads → opzoeken in project.horizontal_line_loads (op .name)
stage.surcharge_loads_left/right → opzoeken in project.surcharge_loads (op .name)
stage.moments          → opzoeken in project.moments          (op .name)
stage.normal_forces    → opzoeken in project.normal_forces    (op .name)
```

Niet-gevonden namen worden als losse tekstrij getoond met "— niet gevonden —".

---

## Aandachtspunten implementatie

- Gebruik `QTableWidget` met `setEditTriggers(NoEditTriggers)` — alleen-lezen
- Stel `setAlternatingRowColors(True)` in voor leesbaarheid
- Kolombreedte: `resizeColumnsToContents()` na vullen
- Lege secties (geen data) tonen een grijs label "— geen data —" in plaats van een lege tabel
- Dezelfde kleurstijl als bestaande tabs (`_HDR_BG`, `_SUBHDR_BG` etc. uit `tab_grondsoorten.py`)
