# Grondsoortentabel zonder fase-dropdown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Het tabblad "Grondsoortentabel" toont alle profielen tegelijk onder elkaar, met een kop per profiel ("1*", "2*", … "X*"), in plaats van een dropdown waarmee één profiel tegelijk wordt getoond.

**Architecture:** `TabGrondsoorten` herstructureren: dropdown weghalen, in `populate()` over alle profielen itereren en voor elk profiel een kop + tabel insertenden in de scroll-container. Bestaande `_maak_tabel()`/`_maak_kolomhoofden()`/`_maak_rij()` blijven hergebruikbaar. Geen wijzigingen aan domeinmodellen, builders of exporters.

**Tech Stack:** PyQt6 (`QVBoxLayout`, `QScrollArea`, `QLabel`).

---

## Bestandsstructuur

**Te wijzigen bestanden:**
- `ui/tabs/tab_grondsoorten.py` — alleen UI; geen domeinwijzigingen

**Niet aanraken:**
- `parsers/models.py:SoilProfile` (model is al goed)
- `reporting/builders/soil_table_builder.py` (rapportage-pad blijft ongewijzigd)
- `app/controller.py` (geen wijzigingen nodig — `populate()` blijft één-aanroep)

---

## Open vragen voor de gebruiker

**Vraag 1: kop-tekst per profiel**
- Optie A: "1*", "2*", … in volgorde van profiel-indexering
- Optie B: profielnaam zoals door D-Sheet gegenereerd (bijv. "Profiel A")
- Optie C: combinatie: "1* — Profiel A"
- Aanbeveling: C — geeft de gebruiker zowel volgordereferentie als context. De `*` markering komt overeen met D-Sheet conventie.

**Vraag 2: tussenruimte / visuele scheiding**
- Tussen tabellen: titel-label + 12px spacing? Horizontale scheidingslijn? Of niets?
- Aanbeveling: titel-label in dezelfde stijl als de huidige header, met 16px ruimte boven elke tabel behalve de eerste.

**Vraag 3: introtekst**
- Huidige `_maak_intro_tekst()` staat éénmaal bovenaan. Behouden bovenaan, of per profiel herhalen?
- Aanbeveling: éénmaal bovenaan; minder herhaling.

---

## Task 1: Dropdown verwijderen, alle profielen renderen

**Files:**
- Modify: `ui/tabs/tab_grondsoorten.py`

- [ ] **Step 1: Verwijder de profielkeuze-rij uit `_build()`**

Verwijder het blok `# ── Profielkeuze ──` (regels ~59-71) inclusief de `QComboBox` en de `currentIndexChanged.connect(...)`.

- [ ] **Step 2: Pas `populate()` aan**

Vervang door iets als:

```python
def populate(self, project: Project | None) -> None:
    """Render alle grondsoortentabellen onder elkaar."""
    self._project = project
    self._clear_content()
    if not project or not project.profiles:
        self._render_leeg()
        return

    intro = self._maak_intro_tekst()
    self._content_layout.insertWidget(self._content_layout.count() - 1, intro)

    soil_map = {s.name: s for s in project.soils}
    for i, profiel in enumerate(project.profiles, start=1):
        kop = self._maak_profiel_kop(i, profiel.name)
        self._content_layout.insertWidget(self._content_layout.count() - 1, kop)
        tabel = self._maak_tabel(profiel, soil_map)
        self._content_layout.insertWidget(self._content_layout.count() - 1, tabel)
```

- [ ] **Step 3: Voeg helper `_maak_profiel_kop()` toe**

```python
def _maak_profiel_kop(self, nummer: int, naam: str) -> QWidget:
    """Maak een sectiekop voor een profiel: '1* — Profielnaam'."""
    lbl = QLabel(f'{nummer}* — {naam}')
    lbl.setStyleSheet(
        f'font-family: {_FONT}; font-size: 13px; font-weight: 600; '
        f'color: {_LABEL_CLR}; background: transparent; '
        f'padding: 16px 4px 6px 4px;'
    )
    return lbl
```

- [ ] **Step 4: Verwijder `_render_profiel()` en `_on_profiel_changed()`**

Deze worden niet meer gebruikt. Controleer dat ze niet elders worden aangeroepen (zou alleen intern moeten zijn).

- [ ] **Step 5: Smoke-test**

Run: `python -c "from ui.tabs.tab_grondsoorten import TabGrondsoorten; print('OK')"`

App starten, project met meerdere profielen laden, controleren dat alle tabellen onder elkaar staan.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: grondsoortentabel toont alle profielen onder elkaar (dropdown vervalt)"
```

---

## Task 2: Tests aanpassen

**Files:**
- `tests/test_tab_grondsoorten.py` als die bestaat — anders overslaan

- [ ] **Step 1: Zoek bestaande tests**

```bash
ls tests/test_tab_grondsoorten.py 2>/dev/null
grep -r "_render_profiel\|_profiel_combo" tests/
```

- [ ] **Step 2: Pas tests aan** als ze de oude API verwachten (dropdown / `_render_profiel`-aanroep) zodat ze de nieuwe `populate()`-flow testen — of voeg een nieuwe test toe die controleert dat na `populate(project)` met N profielen, N tabel-widgets in `_content_layout` staan.

- [ ] **Step 3: Commit**

---

## Acceptatiecriteria

- Tab opent zonder dropdown
- Bij een project met N profielen staan N gestileerde tabellen onder elkaar in de scroll-container
- Elke tabel heeft een kop "1* — Naam", "2* — Naam", …
- Introtekst staat éénmaal bovenaan
- Lege state (geen project) toont nog steeds de bestaande "Geen profieldata"-melding
- Bestaande styling (lettergrootte, randen, kleurenpalet) blijft consistent

## Bekende beperkingen

- Het rapportage-pad (`SoilTableBuilder` → grondsoorten-secties in selectielijst) is NIET geraakt; de tab is alleen UI. Als de rapportage straks ook één-tabel-per-profiel zou moeten worden, is dat een aparte change.
