# Spec: Kwaliteit — Ruff + pre-commit & testdekking uitbreiden

**Datum:** 2026-04-17  
**Status:** Goedgekeurd, gereed voor implementatie

---

## Doel

De codebase heeft geen linter of formatter (12k LoC zonder kwaliteitsbewaking) en ongelijke testdekking: parsers zijn goed gedekt, maar controllers, services, renderers en utilities zijn onbeproefd. Dit plan voegt Ruff toe als linter én formatter via pre-commit, en breidt de testdekking uit naar zes onbedekte gebieden.

---

## Architectuur

```
pyproject.toml              ← ruff-configuratie (linting + formatting)
.pre-commit-config.yaml     ← pre-commit hooks (ruff check + ruff format)

tests/
├── test_ingest_service.py      ← nieuw
├── test_parsing_service.py     ← nieuw
├── test_export_service.py      ← nieuw
├── test_viewport_service.py    ← nieuw
├── test_config_manager.py      ← nieuw
├── test_renderers.py           ← nieuw (headless via FigureCanvasAgg)
├── test_parsers.py             ← bestaand, ongewijzigd
├── test_app_settings.py        ← bestaand, ongewijzigd
└── ...
```

---

## Ruff-configuratie

### `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]

[tool.ruff.format]
quote-style = "double"
```

Regelsets:
- `E` — pycodestyle fouten
- `F` — pyflakes (ongebruikte imports, ongedefinieerde namen)
- `I` — isort (import-volgorde)
- `N` — pep8-naming
- `UP` — pyupgrade (moderniseer Python-syntax)

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Pre-commit flow:**
```
git commit
  → ruff check . --fix   (lint + auto-fix waar mogelijk)
  → ruff format .        (formattering)
  → commit doorgezet indien geen fouten meer
```

### Installatie

```bash
pip install ruff pre-commit
pre-commit install
```

Eerste run op bestaande codebase: `ruff check . --fix` repareert automatisch de meeste stijlwaarschuwingen.

---

## Testdekking

### Teststrategie

- Renderers getest headless via `FigureCanvasAgg` — geen display nodig, werkt in CI
- Services getest met minimale mock-projecten (geen echte `.shi`-bestanden vereist)
- `ConfigManager` getest via pytest `tmp_path` fixture
- Bestaande tests blijven ongewijzigd

### Testplan per gebied

#### `tests/test_ingest_service.py`
- Geldige paden worden correct gegroepeerd op basisnaam
- Ontbrekend bestand geeft `(False, ...)` terug
- Dubbele namen worden samengevoegd in één `FileBundle`

#### `tests/test_parsing_service.py`
- Geldige `FileBundle` produceert een `Project`
- Ongeldige/corrupte bundle geeft `(None, foutmelding)` terug
- `parse_all()` slaat mislukte bundles over, verwerkt succesvolle

#### `tests/test_export_service.py`
- `export_word()` roept `get_exporter('word').export()` aan
- `export_excel()` roept `get_exporter('excel').export()` aan
- Onbekend formaat geeft `(False, ...)` terug
- Getest via mock-exporter geregistreerd in registry

#### `tests/test_viewport_service.py`
- Auto-bounds berekend correct voor project met bekende geometrie
- Zoom-limieten worden gerespecteerd (min/max)
- Lege projecten geven veilige standaardwaarden terug

#### `tests/test_config_manager.py`
- Config laden uit bestaand JSON-bestand
- Ontbrekend bestand geeft standaardconfig terug
- Corrupte JSON wordt afgevangen, geeft standaardconfig terug
- Config opslaan schrijft correct naar schijf (via `tmp_path`)

#### `tests/test_renderers.py`
- `SectionRenderer.render()` crasht niet bij minimaal project (headless)
- `render_output_charts()` crasht niet bij lege resultaten (headless)
- Getest via `matplotlib.use('Agg')` en `FigureCanvasAgg`

---

## Foutafhandeling

- `ruff check --fix` repareert automatisch wat kan
- Resterende fouten blokkeren de commit — ontwikkelaar lost ze handmatig op
- Ruff-fouten zijn geen runtime-fouten: ze blokkeren alleen commits, niet de applicatie
- Pre-commit kan omzeild worden met `git commit --no-verify` (bewust, voor noodgevallen)

---

## Scope & grenzen

**Binnen scope:**
- `pyproject.toml` aanmaken met ruff-configuratie
- `.pre-commit-config.yaml` aanmaken
- Pre-commit installeren en activeren
- Zes nieuwe testbestanden aanmaken
- Bestaande code corrigeren waar ruff fouten meldt

**Buiten scope:**
- 100% testdekking — doel is kritische gebieden afdekken
- CI/CD-integratie (GitHub Actions etc.)
- Typecheck via mypy of pyright
- Docstring-volledigheid controleren
