# Aanvullende Berekeningen Tab — Implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Voeg een nieuwe hoofdtab "Aanvullende berekeningen" toe met een subtab "Hydraulische Grondbreuk" die de NEN 9997-1:2016-controle uitvoert, met auto-invul vanuit het actieve D-Sheet project.

**Architecture:** Twee nieuwe widget-bestanden (`tab_hydraulische_grondbreuk.py` bevat berekeningslogica + UI; `tab_aanvullende_berekeningen.py` is de container met `QTabWidget`). `main_window.py` instantieert de container en roept `update_project()` aan bij project-wissel.

**Tech Stack:** Python 3.10+, PyQt6, bestaande `utils/formatting.py`

---

## Bestandskaart

| Actie | Bestand | Verantwoordelijkheid |
|---|---|---|
| Nieuw | `ui/tabs/tab_hydraulische_grondbreuk.py` | Berekeningslogica + UI voor hydraulische grondbreukcontrole |
| Nieuw | `ui/tabs/tab_aanvullende_berekeningen.py` | Container-widget met interne `QTabWidget` voor subtabs |
| Nieuw | `tests/test_hydraulische_grondbreuk.py` | Unit-tests voor berekeningsfuncties (geen Qt) |
| Wijzig | `app/main_window.py` | Import, instantiatie, tab-toevoeging, `update_project()`-aanroep |

---

## Task 1: Tests voor berekeningslogica

**Files:**
- Create: `tests/test_hydraulische_grondbreuk.py`

- [ ] **Stap 1: Schrijf de falende tests**

```python
"""Tests voor hydraulische grondbreuk berekeningslogica."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.tabs.tab_hydraulische_grondbreuk import (
    bereken_hydraulische_grondbreuk,
    extraheer_auto_waarden,
)
from parsers.models import Project, FileBundle, SheetPilingElement, WaterLevel, Soil


def _maak_project(
    inheiniveau: float = -1.0,
    grondwaterstand: float = 8.0,
    grondgewicht: float = 19.0,
) -> Project:
    damwand = SheetPilingElement(
        name='AZ18', x=0.0, bottom=inheiniveau, top=1.0, width=0.9
    )
    waterpeil = WaterLevel(name='NAP+8', level=grondwaterstand)
    grond = Soil(
        name='Zand', color='rgb(255,220,100)', color_int=None,
        gamma_wet=grondgewicht,
    )
    return Project(
        base_name='test', project_name='Testproject',
        file_bundle=FileBundle(),
        sheet_piling=[damwand],
        waterlevels=[waterpeil],
        soils=[grond],
    )


def test_berekening_voldoet_niet():
    """Rekenvoorbeeld uit Excel: UC = 61,56 / 90,00 = 0,684."""
    p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=2.6,
        inheiniveau=-1.0,
        grondgewicht=19.0,
        grondwaterstand=8.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert abs(p_stab - 61.56) < 0.01
    assert abs(p_water - 90.0) < 0.01
    assert abs(uc - 0.684) < 0.001
    assert uc < 1.0


def test_berekening_voldoet():
    """Situatie met geringe wateropdruk — UC ≥ 1,0."""
    _p_stab, _p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=0.0,
        inheiniveau=-6.0,
        grondgewicht=20.0,
        grondwaterstand=1.0,
        materiaalfactor=1.0,
        watergewicht=10.0,
    )
    assert uc >= 1.0


def test_berekening_nulwaterdruk():
    """Als grondwaterstand gelijk is aan inheiniveau is p_water nul → inf."""
    _p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=0.0,
        inheiniveau=-5.0,
        grondgewicht=19.0,
        grondwaterstand=-5.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert p_water == 0.0
    import math
    assert math.isinf(uc)


def test_extraheer_auto_waarden_volledig():
    """Extraheer inheiniveau, grondwaterstand en grondgewicht uit project."""
    project = _maak_project(inheiniveau=-3.5, grondwaterstand=5.0, grondgewicht=18.5)
    auto = extraheer_auto_waarden(project)
    assert auto.inheiniveau == -3.5
    assert auto.grondwaterstand == 5.0
    assert auto.grondgewicht == 18.5


def test_extraheer_auto_waarden_hoogste_waterpeil():
    """Bij meerdere waterpeilen wordt het hoogste gekozen."""
    damwand = SheetPilingElement(name='AZ', x=0.0, bottom=-2.0, top=1.0, width=0.9)
    grond = Soil(name='Zand', color='rgb(0,0,0)', color_int=None, gamma_wet=19.0)
    project = Project(
        base_name='test', project_name='Test',
        file_bundle=FileBundle(),
        sheet_piling=[damwand],
        waterlevels=[
            WaterLevel(name='Laag', level=2.0),
            WaterLevel(name='Hoog', level=6.0),
            WaterLevel(name='Midden', level=4.0),
        ],
        soils=[grond],
    )
    auto = extraheer_auto_waarden(project)
    assert auto.grondwaterstand == 6.0


def test_extraheer_auto_waarden_leeg_project():
    """Lege lijsten geven None terug — geen crash."""
    project = Project(
        base_name='test', project_name='Test',
        file_bundle=FileBundle(),
    )
    auto = extraheer_auto_waarden(project)
    assert auto.inheiniveau is None
    assert auto.grondwaterstand is None
    assert auto.grondgewicht is None
```

- [ ] **Stap 2: Controleer dat de tests falen**

```
pytest tests/test_hydraulische_grondbreuk.py -v
```

Verwacht: `ImportError` of `ModuleNotFoundError` — bestand bestaat nog niet.

- [ ] **Stap 3: Commit de tests**

```bash
git add tests/test_hydraulische_grondbreuk.py
git commit -m "test: voeg falende tests toe voor hydraulische grondbreuk berekening"
```

---

## Task 2: `TabHydraulischeGrondbreuk` widget

**Files:**
- Create: `ui/tabs/tab_hydraulische_grondbreuk.py`

- [ ] **Stap 1: Maak het bestand aan**

```python
"""Subtab Hydraulische Grondbreuk — controle conform NEN 9997-1:2016."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from parsers.models import Project
from utils.formatting import fmt_number

_MATERIAALFACTOR_STANDAARD = 0.9
_WATERGEWICHT_STANDAARD = 10.0


@dataclass
class AutoWaarden:
    """Waarden die automatisch uit een Project worden ingevuld."""
    inheiniveau: float | None
    grondwaterstand: float | None
    grondgewicht: float | None


def extraheer_auto_waarden(project: Project) -> AutoWaarden:
    """Leid auto-invulwaarden af uit een Project.

    Parameters
    ----------
    project:
        Geparseerd D-Sheet project.

    Returns
    -------
    AutoWaarden
        Inheiniveau, grondwaterstand en grondgewicht, of None als niet beschikbaar.
    """
    inheiniveau = project.sheet_piling[0].bottom if project.sheet_piling else None
    grondwaterstand = (
        max(wl.level for wl in project.waterlevels)
        if project.waterlevels else None
    )
    grondgewicht = project.soils[0].gamma_wet if project.soils else None
    return AutoWaarden(
        inheiniveau=inheiniveau,
        grondwaterstand=grondwaterstand,
        grondgewicht=grondgewicht,
    )


def bereken_hydraulische_grondbreuk(
    bouwputniveau: float,
    inheiniveau: float,
    grondgewicht: float,
    grondwaterstand: float,
    materiaalfactor: float,
    watergewicht: float,
) -> tuple[float, float, float]:
    """Bereken de hydraulische grondbreukcontrole conform NEN 9997-1:2016.

    Parameters
    ----------
    bouwputniveau:   Ontgravingsniveau bouwput [m NAP].
    inheiniveau:     Onderkant damwand [m NAP].
    grondgewicht:    Volumegewicht grond γ [kN/m³].
    grondwaterstand: Grondwaterstand buiten bouwput [m NAP].
    materiaalfactor: Materiaalfactor ψ [-].
    watergewicht:    Volumegewicht water γ_w [kN/m³].

    Returns
    -------
    tuple[float, float, float]
        (P_stab [kN/m²], P_water [kN/m²], UC [-]).
        UC is inf als P_water nul is.
    """
    dikte_grondwig = bouwputniveau - inheiniveau
    p_stab = dikte_grondwig * grondgewicht * materiaalfactor
    p_water = (grondwaterstand - inheiniveau) * watergewicht
    uc = p_stab / p_water if p_water != 0.0 else math.inf
    return p_stab, p_water, uc


class TabHydraulischeGrondbreuk(QWidget):
    """Subtab met hydraulische grondbreukcontrole (NEN 9997-1:2016)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._auto_waarden: AutoWaarden | None = None
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self._bouw_invoergroep())
        layout.addWidget(self._bouw_resultaatgroep())
        layout.addStretch()
        self._verbind_signalen()
        self._herbereken()

    def _bouw_invoergroep(self) -> QGroupBox:
        groep = QGroupBox('Invoer')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._spin_bouwput = self._maak_spin(-50.0, 50.0, 2)
        self._spin_inhei = self._maak_spin(-50.0, 50.0, 2)
        self._spin_grondgewicht = self._maak_spin(0.0, 40.0, 1)
        self._spin_grondwater = self._maak_spin(-50.0, 50.0, 2)
        self._spin_materiaalfactor = self._maak_spin(0.0, 2.0, 2)
        self._spin_watergewicht = self._maak_spin(0.0, 20.0, 1)

        self._spin_materiaalfactor.setValue(_MATERIAALFACTOR_STANDAARD)
        self._spin_watergewicht.setValue(_WATERGEWICHT_STANDAARD)

        self._btn_reset_inhei = self._maak_reset_knop()
        self._btn_reset_grondwater = self._maak_reset_knop()
        self._btn_reset_grondgewicht = self._maak_reset_knop()

        rijen: list[tuple[str, QDoubleSpinBox, QPushButton | None]] = [
            ('Bouwputniveau (m NAP)', self._spin_bouwput, None),
            ('Inheiniveau damwand (m NAP)', self._spin_inhei, self._btn_reset_inhei),
            ('Grondgewicht γ (kN/m³)', self._spin_grondgewicht, self._btn_reset_grondgewicht),
            ('Grondwaterstand buiten (m NAP)', self._spin_grondwater, self._btn_reset_grondwater),
            ('Materiaalfactor ψ (–)', self._spin_materiaalfactor, None),
            ('Watergewicht γ_w (kN/m³)', self._spin_watergewicht, None),
        ]
        for rij, (label_tekst, spin, reset) in enumerate(rijen):
            grid.addWidget(QLabel(label_tekst), rij, 0)
            grid.addWidget(spin, rij, 1)
            if reset is not None:
                grid.addWidget(reset, rij, 2)

        return groep

    def _bouw_resultaatgroep(self) -> QGroupBox:
        groep = QGroupBox('Resultaat')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._lbl_p_stab = QLabel('-')
        self._lbl_p_water = QLabel('-')
        self._lbl_uc = QLabel('-')

        font_groot = QFont()
        font_groot.setPointSize(14)
        font_groot.setBold(True)
        self._lbl_uc.setFont(font_groot)

        self._lbl_status = QLabel('–')
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setMinimumHeight(44)

        grid.addWidget(QLabel('Stabiliserende druk'), 0, 0)
        grid.addWidget(self._lbl_p_stab, 0, 1)
        grid.addWidget(QLabel('Aandrijvende waterdruk'), 1, 0)
        grid.addWidget(self._lbl_p_water, 1, 1)
        grid.addWidget(QLabel('Gebruiksgraad (UC)'), 2, 0)
        grid.addWidget(self._lbl_uc, 2, 1)
        grid.addWidget(self._lbl_status, 3, 0, 1, 2)

        return groep

    def _maak_spin(self, minimum: float, maximum: float, decimalen: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimalen)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(110)
        return spin

    def _maak_reset_knop(self) -> QPushButton:
        btn = QPushButton('↺')
        btn.setFixedWidth(30)
        btn.setToolTip('Terugzetten naar projectwaarde')
        return btn

    def _verbind_signalen(self) -> None:
        for spin in [
            self._spin_bouwput, self._spin_inhei, self._spin_grondgewicht,
            self._spin_grondwater, self._spin_materiaalfactor, self._spin_watergewicht,
        ]:
            spin.valueChanged.connect(self._herbereken)
        self._btn_reset_inhei.clicked.connect(self._reset_inhei)
        self._btn_reset_grondwater.clicked.connect(self._reset_grondwater)
        self._btn_reset_grondgewicht.clicked.connect(self._reset_grondgewicht)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------
    def update_project(self, project: Project | None) -> None:
        """Vul invoervelden automatisch in vanuit project.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        if project is None:
            self._auto_waarden = None
            return
        self._auto_waarden = extraheer_auto_waarden(project)
        self._reset_inhei()
        self._reset_grondwater()
        self._reset_grondgewicht()

    # ------------------------------------------------------------------
    # Reset-handlers
    # ------------------------------------------------------------------
    def _reset_inhei(self) -> None:
        if self._auto_waarden and self._auto_waarden.inheiniveau is not None:
            self._spin_inhei.blockSignals(True)
            self._spin_inhei.setValue(self._auto_waarden.inheiniveau)
            self._spin_inhei.blockSignals(False)
        self._herbereken()

    def _reset_grondwater(self) -> None:
        if self._auto_waarden and self._auto_waarden.grondwaterstand is not None:
            self._spin_grondwater.blockSignals(True)
            self._spin_grondwater.setValue(self._auto_waarden.grondwaterstand)
            self._spin_grondwater.blockSignals(False)
        self._herbereken()

    def _reset_grondgewicht(self) -> None:
        if self._auto_waarden and self._auto_waarden.grondgewicht is not None:
            self._spin_grondgewicht.blockSignals(True)
            self._spin_grondgewicht.setValue(self._auto_waarden.grondgewicht)
            self._spin_grondgewicht.blockSignals(False)
        self._herbereken()

    # ------------------------------------------------------------------
    # Berekening
    # ------------------------------------------------------------------
    def _herbereken(self) -> None:
        p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
            bouwputniveau=self._spin_bouwput.value(),
            inheiniveau=self._spin_inhei.value(),
            grondgewicht=self._spin_grondgewicht.value(),
            grondwaterstand=self._spin_grondwater.value(),
            materiaalfactor=self._spin_materiaalfactor.value(),
            watergewicht=self._spin_watergewicht.value(),
        )
        self._lbl_p_stab.setText(f'{fmt_number(p_stab, 2)} kN/m²')
        self._lbl_p_water.setText(f'{fmt_number(p_water, 2)} kN/m²')
        uc_tekst = fmt_number(uc, 3) if not math.isinf(uc) else '∞'
        self._lbl_uc.setText(uc_tekst)

        voldoet = uc >= 1.0
        status_tekst = 'VOLDOET' if voldoet else 'VOLDOET NIET'
        kleur = '#2e7d32' if voldoet else '#c62828'
        self._lbl_status.setText(status_tekst)
        self._lbl_status.setStyleSheet(
            f'background-color: {kleur}; color: white; font-weight: bold;'
            f' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )
```

- [ ] **Stap 2: Draai de tests — ze moeten nu slagen**

```
pytest tests/test_hydraulische_grondbreuk.py -v
```

Verwacht: alle 6 tests PASS.

- [ ] **Stap 3: Commit**

```bash
git add ui/tabs/tab_hydraulische_grondbreuk.py
git commit -m "feat: voeg TabHydraulischeGrondbreuk widget en berekeningslogica toe"
```

---

## Task 3: `TabAanvullendeBerekeningen` container

**Files:**
- Create: `ui/tabs/tab_aanvullende_berekeningen.py`

- [ ] **Stap 1: Maak het bestand aan**

```python
"""Hoofdtab Aanvullende berekeningen — container voor aanvullende geotechnische controles."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from parsers.models import Project
from ui.tabs.tab_hydraulische_grondbreuk import TabHydraulischeGrondbreuk


class TabAanvullendeBerekeningen(QWidget):
    """Container-tab met subtabs voor aanvullende geotechnische berekeningen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tab_hydraulische_grondbreuk = TabHydraulischeGrondbreuk()
        self._tabs.addTab(self._tab_hydraulische_grondbreuk, 'Hydraulische Grondbreuk')

        layout.addWidget(self._tabs)

    def update_project(self, project: Project | None) -> None:
        """Propageer projectwijziging naar alle subtabs.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        self._tab_hydraulische_grondbreuk.update_project(project)
```

- [ ] **Stap 2: Controleer dat bestaande tests nog slagen**

```
pytest tests/ -v
```

Verwacht: alle tests PASS (geen regressies).

- [ ] **Stap 3: Commit**

```bash
git add ui/tabs/tab_aanvullende_berekeningen.py
git commit -m "feat: voeg TabAanvullendeBerekeningen container toe"
```

---

## Task 4: Integreer in `main_window.py`

**Files:**
- Modify: `app/main_window.py`

De wijzigingen zijn op vier plekken in `main_window.py`:

1. Import toevoegen (bij de bestaande tab-imports ~regel 39–48)
2. Instantiatie + `addTab` (bij de tab-opbouw ~regel 195–197, vóór de "Instellingen"-tab)
3. `update_project()` aanroepen in `_update_all()` (~regel 624)
4. `update_project(None)` aanroepen in `_on_reset()` (~regel 319)

- [ ] **Stap 1: Voeg import toe**

Zoek in `app/main_window.py` naar:
```python
from ui.tabs.tab_grondsoorten import TabGrondsoorten
```

Voeg er direct onder toe:
```python
from ui.tabs.tab_aanvullende_berekeningen import TabAanvullendeBerekeningen
```

- [ ] **Stap 2: Instantieer en voeg toe als tab**

Zoek naar:
```python
        # Tab 5: Instellingen
        self._tab_instellingen = TabInstellingen()
        self._main_tabs.addTab(self._tab_instellingen, 'Instellingen')
```

Voeg er direct vóór in:
```python
        # Tab 5: Aanvullende berekeningen
        self._tab_aanvullende_berekeningen = TabAanvullendeBerekeningen()
        self._main_tabs.addTab(self._tab_aanvullende_berekeningen, 'Aanvullende berekeningen')

```

- [ ] **Stap 3: Aanroepen bij project-update**

Zoek naar:
```python
    def _update_all(self) -> None:
        self._btn_export_rapport.setEnabled(bool(self._state.projects))
        self._update_render_views()
        self._refresh_active_report_tab()
        self._update_preview()
```

Vervang door:
```python
    def _update_all(self) -> None:
        self._btn_export_rapport.setEnabled(bool(self._state.projects))
        self._update_render_views()
        self._refresh_active_report_tab()
        self._update_preview()
        self._tab_aanvullende_berekeningen.update_project(
            self._state.get_active_project()
        )
```

- [ ] **Stap 4: Aanroepen bij reset**

Zoek naar:
```python
    def _on_reset(self) -> None:
        self._controller.reset()
        self._tab_report_context.refresh_projects({})
```

Voeg toe na `self._controller.reset()`:
```python
        self._tab_aanvullende_berekeningen.update_project(None)
```

Dus:
```python
    def _on_reset(self) -> None:
        self._controller.reset()
        self._tab_aanvullende_berekeningen.update_project(None)
        self._tab_report_context.refresh_projects({})
```

- [ ] **Stap 5: Draai alle tests**

```
pytest tests/ -v
```

Verwacht: alle tests PASS.

- [ ] **Stap 6: Start de applicatie en controleer visueel**

```
python run.pyw
```

Controleer:
- Tab "Aanvullende berekeningen" zichtbaar vóór "Instellingen"
- Subtab "Hydraulische Grondbreuk" correct weergegeven
- Invoervelden tonen standaardwaarden
- Resultaat wordt direct berekend
- Importeer een `.shi`-bestand → inheiniveau, grondwaterstand en grondgewicht worden automatisch ingevuld
- Wijzig een veld handmatig → herberekening direct zichtbaar
- Druk op ↺ → projectwaarde wordt hersteld
- Druk op Reset (Rapportcontext-tab) → `update_project(None)` wordt aangeroepen (velden blijven op vorige waarde, geen crash)

- [ ] **Stap 7: Commit**

```bash
git add app/main_window.py
git commit -m "feat: integreer Aanvullende berekeningen tab in main_window"
```
