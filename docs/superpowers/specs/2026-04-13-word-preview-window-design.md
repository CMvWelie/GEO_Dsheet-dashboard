# Word Preview Window — Ontwerpdocument

**Datum:** 2026-04-13  
**Status:** Goedgekeurd  

---

## Samenvatting

Een zwevend Word-preview venster dat naast de hoofdapplicatie kan worden geplaatst en automatisch een HTML-weergave toont van het te exporteren rapport (alleen de geselecteerde secties). Het template-pad wordt persistent opgeslagen via een nieuw Instellingen-tabje.

---

## Beslissingen

| Vraag | Keuze |
|---|---|
| Locatie preview | Apart zwevend `QMainWindow`-venster |
| Weergave | HTML-rapportweergave (geen echte Word/PDF-rendering) |
| Vernieuwen | Automatisch bij elke `_update_all()` aanroep |
| Zichtbare secties | Alleen geselecteerde rapport-items |
| Template-pad | Persistent via nieuw Instellingen-tabje |

> Optie B (echte .docx → PDF rendering) is bewust uitgesteld als toekomstige uitbreiding.

---

## Nieuwe bestanden

### `ui/preview_window.py` — `WordPreviewWindow(QMainWindow)`

Zwevend venster met:
- `QTextBrowser` voor HTML-weergave (scrollbaar, linkvrij)
- Smalle statusbalk met aantal geselecteerde secties en tijdstip van laatste update
- Methode `set_html(html: str) -> None` — enige publieke API
- Venster onthoudt positie/grootte via `QSettings`
- Sluit zichzelf niet bij sluiten van hoofdvenster (blijft open tot gebruiker het sluit)

Het venster is bewust "dom": geen toegang tot `AppState`, geen logica. Ontvangt alleen een HTML-string.

### `ui/tabs/tab_instellingen.py` — `TabInstellingen(QWidget)`

Nieuw tabblad "Instellingen" met:
- **Groep "Rapportage-instellingen"**: bladerbalk voor Word-template (`.docx`), persistent pad, wis-knop
- **Groep "Preview-venster"**: knop "↗ Preview openen" die `preview_open_requested` signal afvuurt
- Placeholder voor toekomstige instellingen (bedrijfsnaam, logo, kleurpalet)
- Signalen: `template_path_changed = pyqtSignal(str)`, `preview_open_requested = pyqtSignal()`
- Publieke methode `set_template_path(path: str) -> None` — aangeroepen vanuit `main_window.py` na config-load om het opgeslagen pad te tonen

### `reporting/builders/html_preview_builder.py` — `HtmlPreviewBuilder`

Klasse die een `ReportPackage` omzet naar een HTML-string voor weergave in `QTextBrowser`.

```
build(package: ReportPackage) -> str
```

Genereert:
- Rapporttitel als kop
- Per geselecteerde sectie: sectiontitel + tabel of tekstvelden
- Stijl consistent met de bestaande marine-blauw kleurpalette (`#1b3a5c`, `#274f77`)
- Inline CSS (geen externe bestanden — `QTextBrowser` ondersteunt geen externe stylesheets)

---

## Gewijzigde bestanden

### `app/settings.py`

Nieuwe dataclass toevoegen:

```python
@dataclass
class AppSettings:
    word_template_path: str = ''
```

### `app/config_manager.py`

- `load()` returntype uitbreiden: `tuple[RenderSettings, ViewportSettings, AppSettings]`
- `save()` signature uitbreiden met `app_settings: AppSettings`
- Sleutel `'app_settings'` toegevoegd aan het JSON-config-bestand

### `app/app_state.py`

```python
app_settings: AppSettings = field(default_factory=AppSettings)
```

### `app/app_controller.py`

Nieuwe methode:

```python
def apply_app_settings(self, settings: AppSettings) -> None:
    """Sla app-instellingen op in state en config."""
```

- Schrijft naar `self._state.app_settings`
- Roept `ConfigManager.save()` aan
- `WordExporter` gebruikt `AppState.app_settings.word_template_path` als fallback wanneer het Word-export-tabje geen eigen pad heeft ingevuld

### `app/main_window.py`

- `TabInstellingen` instantiëren en toevoegen aan `_main_tabs`
- `WordPreviewWindow` aanmaken als attribuut (`self._preview_window`)
- `_connect_signals()` uitbreiden:
  - `tab_instellingen.template_path_changed` → `controller.apply_app_settings()`
  - `tab_instellingen.preview_open_requested` → `_on_preview_open()`
- `_update_all()` uitbreiden:
  - Als `self._preview_window.isVisible()`: bouw HTML via `HtmlPreviewBuilder` en roep `set_html()` aan

---

## Dataflow

```
App start
  → ConfigManager.load() → AppState.app_settings (word_template_path)
  → TabInstellingen toont opgeslagen pad

Template-pad gewijzigd
  → TabInstellingen.template_path_changed
  → AppController.apply_app_settings()
  → AppState.app_settings bijgewerkt + ConfigManager.save()

Preview openen
  → TabInstellingen.preview_open_requested
  → MainWindow._on_preview_open()
  → WordPreviewWindow.show()
  → direct _update_preview() aanroepen (eerste render)

Rapport-selectie / project wijzigt
  → AppController._update_all()
  → _update_preview() (alleen als venster zichtbaar)
  → HtmlPreviewBuilder.build(package) → HTML string
  → WordPreviewWindow.set_html(html)

Word-export
  → WordExporter gebruikt app_settings.word_template_path
    als TabWordExport geen eigen pad heeft ingevuld
```

---

## Wat bewust buiten scope valt

- **PDF-rendering** (optie B): vereist LibreOffice of Microsoft Word; bewaard als toekomstige uitbreiding
- **Zoom-instelling** in de preview: kan later als slider in de statusbalk
- **Bedrijfsinstellingen** (naam, logo): placeholder in Instellingen-tab, implementatie later
- **Print-knop** vanuit preview-venster: valt buiten scope van dit ontwerp

---

## Aannames

- `ReportPackage` is al beschikbaar via `ReportController` op het moment dat `_update_all()` wordt aangeroepen
- `QTextBrowser` ondersteunt de gebruikte HTML/CSS voldoende (tabellen, inline stijlen, kopniveaus)
- Het Word-export-tabje behoudt zijn eigen pad-veld; `app_settings.word_template_path` is enkel een persistente fallback
