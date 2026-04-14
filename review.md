# D-Sheet Dashboard — Code Review (2026-04-14)

Gegenereerd via adversarial review door Claude Code + Codex Explore agent.

---

## 1. Kritieke Bugs

| # | Bestand | Regel | Probleem |
|---|---------|-------|---------|
| 1.1 | `app/controller.py` | ~237 | Parameter `stage` mist type hint — `None` kan ongemerkt binnenkomen |
| 1.2 | `renderers/output_renderer.py` | 147–150 | `.index()` op mogelijk lege lijst → **IndexError crash** |
| 1.3 | `app/controller.py` | ~253 | Bare `except Exception: return None` — fouten verdwijnen zonder spoor |
| 1.4 | `exporters/excel_exporter.py` / `word_exporter.py` | ~87 | Zelfde silent swallowing in exporters |
| 1.5 | `renderers/section_renderer.py` | ~813 | Tuple kleurformaat gemengd met string `'rgba(...)'` — inconsistent |
| 1.6 | `renderers/section_renderer.py` | ~236 | Arc-hoeken `-99, 99` moeten `-90, 90` zijn — momentensymbool is verkeerd |

---

## 2. Architectuurschendingen

### 2.1 — `OutputRenderer` is geen `BaseRenderer` subclass
`render_output_charts()` is een losse module-functie. De design rule vereist een `BaseRenderer` subclass. Dit is de meest impactvolle schending.

### 2.2 — Circular import risico
`renderers/section_renderer.py` importeert uit `renderers/__init__.py`. Als `__init__.py` ooit `section_renderer` importeert, circulaire dependency.

### 2.3 — Optionele dependencies pas gecontroleerd bij gebruik
`openpyxl` en `python-docx` worden afgevangen met `try/except ImportError` diep in de exporter — de gebruiker krijgt pas een foutmelding als hij probeert te exporteren. Beter: check bij app-start.

### 2.4 — `blockSignals()` patroon in view is fragiel
`_sync_viewport_spinboxes()` in `main_window.py` blokkeert handmatig Qt-signalen. Werkt, maar breekt makkelijk bij refactoring.

---

## 3. Matige Issues

- **Stage-index zonder bovengrens**: `set_active_stage()` clipped alleen op `0`, niet op `len(stages)-1` → potentiële `IndexError`
- **Duplicate code**: `_build_layer_polygon()` in `section_renderer.py` bestaat ook in `utils/geometry.py`
- **Hardcoded magic numbers**: venstergrootte `1600×950`, achtergrondkleur `#ecebd8`, pijlhoogte `0.3` — allemaal in code, niet configureerbaar
- **Geen logging**: Alle fouten gaan via `return str(exc)` of worden gesmoord — geen traceerbaarheid

---

## 4. Verbetervoorstellen Architectuur

### Voorstel A — Logging framework
```python
import logging
logger = logging.getLogger(__name__)
# Vervang: except Exception: return None
# Door:    except Exception as exc: logger.exception("..."); return None
```

### Voorstel B — `OutputRenderer` als klasse
```python
class OutputRenderer(BaseRenderer):
    def render(self, ax, project, stage, settings, viewport) -> None:
        ...  # huidige render_output_charts inhoud
```

### Voorstel C — Stage-index validatie
```python
def set_active_stage(self, index: int) -> None:
    n = len((self._state.get_active_project().stages or []))
    self._state.active_stage_index = max(0, min(index, n - 1))
```

### Voorstel D — Startup dependency check
```python
# In app/__init__.py of main_window.py __init__
for pkg, name in [('openpyxl', 'Excel export'), ('docx', 'Word export')]:
    if importlib.util.find_spec(pkg) is None:
        warnings.warn(f'{name} niet beschikbaar: pip install {pkg}')
```

---

## 5. Prioriteitenlijst

| Prioriteit | Actie | Tijd |
|-----------|-------|------|
| **1** | Fix IndexError in `output_renderer.py:147` | 15 min |
| **2** | Fix arc-hoeken `-99→-90` in `section_renderer.py:236` | 5 min |
| **3** | Stage-index bovengrens in `controller.py` | 15 min |
| **4** | Logging toevoegen aan exceptions | 1–2 uur |
| **5** | `OutputRenderer` refactor naar `BaseRenderer` | 2 uur |
| **6** | Duplicate `_build_layer_polygon()` verwijderen | 30 min |

---

## 6. Status

- [ ] Prioriteit 1 — Fix IndexError output_renderer
- [ ] Prioriteit 2 — Fix arc-hoeken section_renderer
- [ ] Prioriteit 3 — Stage-index bovengrens
- [ ] Prioriteit 4 — Logging framework
- [ ] Prioriteit 5 — OutputRenderer refactor
- [ ] Prioriteit 6 — Duplicate geometry code opruimen
