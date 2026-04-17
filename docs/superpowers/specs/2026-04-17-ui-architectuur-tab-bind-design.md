# Spec: UI-architectuur — main_window afslanken via tab.bind()

**Datum:** 2026-04-17  
**Status:** Goedgekeurd, gereed voor implementatie

---

## Doel

`main_window.py` groeit lineair met elke nieuwe tab doordat alle signaalverbindingen centraal in `_connect_signals()` worden gelegd. Elke tab krijgt een `bind(controller, signals)`-methode die zijn eigen verbindingen beheert. `main_window` wordt een dunne orkestrator.

---

## Architectuur

```
app/
├── signals.py          ← AppSignals(QObject) — alle app-signalen
├── controller.py       ← Qt-vrij, ontvangt AppSignals als dependency
└── main_window.py      ← instantieert AppSignals, roept tab.bind() aan

ui/tabs/
├── tab_*.py            ← elke tab implementeert bind(controller, signals)
```

---

## Componenten

### `app/signals.py`

```python
from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    project_gewijzigd = pyqtSignal(str)
    fase_gewijzigd = pyqtSignal(int)
    render_bijgewerkt = pyqtSignal()
    bestanden_verwerkt = pyqtSignal()
    instellingen_gewijzigd = pyqtSignal()
```

Nieuwe signalen worden hier toegevoegd — één plek, geen verspreiding.

### `app/controller.py`

Ontvangt `AppSignals` als constructor-parameter. Emitteert signalen na state-mutaties:

```python
class AppController:
    def __init__(self, state: AppState, signals: AppSignals) -> None:
        self._state = state
        self._signals = signals

    def set_active_project(self, naam: str) -> None:
        self._state.active_project = naam
        self._signals.project_gewijzigd.emit(naam)
```

Controller blijft Qt-vrij: `AppSignals` wordt als dependency geïnjecteerd, niet geïmporteerd voor gebruik.

### Elke tab-klasse (`ui/tabs/tab_*.py`)

```python
class TabGrondsoorten(QWidget):
    def bind(self, controller: AppController, signals: AppSignals) -> None:
        self._controller = controller
        signals.project_gewijzigd.connect(self._on_project_gewijzigd)
        signals.bestanden_verwerkt.connect(self._vernieuw)
```

- `bind()` wordt eenmalig aangeroepen na constructie
- Elke tab verbindt alleen de signalen die relevant zijn
- Geen dubbele verbindingen — `bind()` wordt nooit twee keer aangeroepen

### `app/main_window.py`

```python
def __init__(self) -> None:
    self._signals = AppSignals()
    self._controller = AppController(self._state, self._signals)
    self._build()
    self._bind_tabs()

def _bind_tabs(self) -> None:
    for tab in self._alle_tabs:
        tab.bind(self._controller, self._signals)
```

- `_connect_signals()` verdwijnt volledig
- `_bind_tabs()` vervangt het — schaalbaar, geen handmatige bedrading per tab
- `_on_main_tab_changed()` blijft voor on-demand refresh van actieve tab
- Geen directe signaalverbindingen meer in `main_window`

---

## Data flow

```
Gebruiker selecteert project
  → main_window._on_project_geselecteerd()
  → controller.set_active_project(naam)
  → signals.project_gewijzigd.emit(naam)
  → alle geabonneerde tabs reageren onafhankelijk

Nieuwe tab toevoegen
  → tab_nieuw.py: implementeer bind()
  → main_window: voeg tab toe aan self._alle_tabs
  → geen andere wijzigingen nodig
```

---

## Foutafhandeling

- Signalen hebben geen retourwaarde — fouten in tab-handlers worden lokaal afgevangen via `QMessageBox.warning()`
- Controller retourneert `tuple[bool, str]` bij actie-aanroepen; `main_window` toont fout indien nodig
- `bind()` mag nooit falen — geen conditionele verbindingen, geen try/except

---

## Testen

| Testbestand | Wat wordt getest |
|---|---|
| `tests/test_app_signals.py` | Signaal emitteert, verbonden slot wordt aangeroepen |
| `tests/test_tab_bind.py` | Elke tab verbindt correct in `bind()`, geen dubbele verbindingen |
| Handmatig | Golden path: project selecteren → alle tabs bijgewerkt |

---

## Scope & grenzen

**Binnen scope:**
- `app/signals.py` aanmaken met `AppSignals`
- `AppController` ontvangt `AppSignals` als dependency
- Alle 10 tabs implementeren `bind(controller, signals)`
- `main_window._connect_signals()` vervangen door `_bind_tabs()`

**Buiten scope:**
- Wijzigingen aan tab-logica zelf
- On-demand refresh-logica (`_on_main_tab_changed`)
- Nieuwe signalen buiten de huidige set
