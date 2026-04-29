# App-styling en multi-template-systeem

**Datum:** 2026-04-29
**Status:** Ontwerp goedgekeurd, klaar voor implementatieplan

## Doel

De UI van D-Sheet Dashboard krijgt een centraal thema-systeem dat aansluit op de DKIB-huisstijl (uit `DKIB_TEMPLATE.xltx`) en uitbreidbaar is naar andere bedrijfsprofielen (zoals SixGeoConsult). Het systeem vervangt de gedupliceerde inline `_BTN_PRIMARY`/`_BTN_NORMAL`/`_CARD_STYLE`-constanten in elke tab door één bron van waarheid.

In deze ronde wordt het systeem **opgezet** en **gepiloteerd op Tab Rapportcontext** (Tab 0). De overige 9 tabs blijven hun lokale stijlconstanten houden tot een vervolg-iteratie.

## Achtergrond

De applicatie bevat 30+ bestanden met `setStyleSheet()` en 12 bestanden waar dezelfde `_BTN_PRIMARY`/`_CARD_STYLE`-constanten woord voor woord zijn gedupliceerd, met onderlinge variaties (paddings 4-14px, font-sizes 10-12px, border-radii 5-8px). De Eina04-fonts en `DKIB_logo.png` staan al in `C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/` maar worden door de app niet gebruikt. De huidige primaire kleur `#245b7a` komt niet overeen met het DKIB-accentblauw `#147ACF` uit de Excel-template.

## Architectuur

Het systeem wordt opgesplitst conform de "no Qt in controllers"-regel uit `CLAUDE.md`:

| Module | Verantwoordelijkheid | Qt? |
|---|---|---|
| `app/theme.py` | `Theme` dataclass, JSON-loader, stylesheet-string-generator, `discover_themes()` | nee |
| `app/theme_apply.py` | `QFontDatabase.addApplicationFont()`, `QApplication.setStyleSheet()`, `bootstrap_theme()` | ja |
| `themes/dkib.json` | Default thema, absolute paden naar `00 Algemeen` | n.v.t. |
| `themes/sixgeoconsult.json` | Tweede thema ter validatie multi-template | n.v.t. |

`AppSettings` krijgt één extra veld `active_theme_name: str` (default `"DKIB"`). `ConfigManager` slaat dit veld op tussen sessies. Bij opstarten leest `run.pyw` dit, laadt het bijbehorende JSON-thema, registreert fonts, en past de stylesheet toe — alles vóór `MainWindow()` geconstrueerd wordt.

**Theme-wissel = herstart vereist.** De Instellingen-tab toont een info-message bij wijziging.

## Theme JSON-schema

```json
{
  "name": "DKIB",
  "colors": {
    "primary": "#147ACF",
    "primary_hover": "#0d63ad",
    "primary_pressed": "#0a4f8a",
    "text": "#44546A",
    "text_muted": "#7a8794",
    "border": "#D8DFE6",
    "border_strong": "#aabdca",
    "surface": "#FFFFFF",
    "background": "#FAFBFC",
    "ok": "#309942",
    "warning": "#FF5C00",
    "danger": "#c0392b"
  },
  "typography": {
    "family": "Eina 04",
    "fallback": "Segoe UI",
    "size_base": 11,
    "size_title": 12,
    "size_small": 10
  },
  "geometry": {
    "radius": 4,
    "spacing": 8,
    "padding_button": "7px 14px"
  },
  "assets": {
    "font_files": [
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-Regular.ttf",
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-SemiBold.ttf",
      "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/Eina04-Bold.ttf"
    ],
    "app_logo": "C:/Users/t.vanwelie/Dropbox/DKIB_geotechniek/00 Algemeen/DKIB_logo.png"
  }
}
```

**Validatie en fouttolerantie:**
- Bij `Theme.load(path)` worden de drie top-level keys (`colors`, `typography`, `geometry`) verplicht; `assets` is optioneel. Bij ontbrekende key raised `Theme.load()` een `ValueError`.
- Wanneer een bestand uit `font_files` niet bestaat (pad ongeldig, font verplaatst): warning naar stderr, font wordt overgeslagen, fallback (`Segoe UI`) wordt gebruikt.
- Wanneer `app_logo` niet bestaat: cornerwidget toont geen logo, geen crash.
- Wanneer het actieve themabestand ontbreekt of `Theme.load()` faalt: `bootstrap_theme()` valt terug op `themes/dkib.json` (de gebundelde default). Faalt die ook, dan past `bootstrap_theme()` géén stylesheet toe — de app start met Qt-defaults zodat de gebruiker de Instellingen-tab nog kan bereiken.

## Stylesheet-generator

`Theme.build_stylesheet() -> str` genereert één app-wide QSS-string. Deze regelt:

- **QPushButton** algemeen + per `objectName`:
  - `QPushButton#btnPrimary` — gevuld primair
  - `QPushButton#btnNormal` — wit met border
  - `QPushButton#btnDanger` — wit met rode border en tekst
  - `QPushButton#btnClear` — kleine wis-knop (gebruikt voor `✕`)
- **QGroupBox** — card-stijl met radius en titel-positionering
- **QLineEdit** + **QComboBox** + **QDoubleSpinBox** — uniforme borders
- **QTabWidget** + **QTabBar::tab** — actieve tab krijgt `border-top: 3px solid primary`, samen met `QTabWidget::pane { border-top: 1px solid border; top: -1px; }` om dubbele lijn op Windows te voorkomen
- **QLabel** — basislettertype/kleur
- **QListWidget** + **QFrame** — neutrale styling

De gegenereerde string gebruikt de **werkelijke font-familienaam** zoals teruggegeven door `QFontDatabase.applicationFontFamilies()`. Daarom werkt de stylesheet-generator in twee stappen:

1. `Theme.load()` parsed de JSON en houdt het pad naar de fonts vast.
2. `theme_apply.bootstrap_theme()` registreert de fonts via Qt, vraagt de werkelijke familienaam op, geeft die door aan `Theme.build_stylesheet(actual_family)`, en past het resultaat toe op de `QApplication`.

## Bootstrap-volgorde in `run.pyw`

```
sys.path-setup
QApplication(sys.argv)
theme_apply.bootstrap_theme(config.active_theme_name)
MainWindow()
app.exec()
```

`bootstrap_theme` doet intern:
1. Laad `themes/<naam>.json` via `Theme.load()`. Bij falen → fallback-thema.
2. Voor elk pad in `assets.font_files`: `QFontDatabase.addApplicationFont(path)`. Bij `-1` → warning + skip.
3. Bepaal werkelijke font-familienaam uit het eerste succesvol geladen TTF; bij geen succes → `typography.fallback`.
4. Genereer stylesheet via `Theme.build_stylesheet(actual_family)`.
5. `QApplication.instance().setStyleSheet(stylesheet)`.
6. Geef het geladen `Theme`-object terug; `MainWindow` ontvangt het via constructor (voor het app-logo en eventuele toekomstige uitbreidingen).

## Pilot: Tab Rapportcontext

**Wijzigingen in `ui/tabs/tab_report_context.py`:**
- Verwijder lokale `_BTN_PRIMARY` en `_BTN_DANGER` constanten.
- Geef de import-knop `objectName = "btnPrimary"`, de reset-knop `objectName = "btnDanger"`, de bladeren/wissen-knoppen `objectName = "btnNormal"`.
- Verwijder inline `setStyleSheet()` op het logo-vakje en het label `"Project:"`. De QGroupBox-cards en QLineEdit-velden krijgen hun nieuwe stijl automatisch via de globale stylesheet (geen lokale code nodig).

**Wijzigingen in `app/main_window.py`:**
- Aan de tab-balk wordt via `setCornerWidget(widget, Qt.Corner.TopLeftCorner)` een kleine `QLabel` toegevoegd met het thema-app-logo (`assets.app_logo`), geschaald naar maximaal 28px hoogte met behoud van aspect ratio. Bij ontbrekend of niet-laadbaar logo wordt geen cornerwidget gezet (geen placeholder).
- De bestaande rechter cornerwidget (project-dropdown + "Exporteer rapport"-knop) blijft functioneel ongewijzigd; alleen de inline `_BTN_PRIMARY` op de export-knop wordt vervangen door `objectName = "btnPrimary"` (en de `setStyleSheet`-aanroep verwijderd).
- De moduleconstanten `_CARD_STYLE`, `_BTN_PRIMARY`, `_BTN_NORMAL`, `_BTN_DANGER` bovenaan `main_window.py` blijven bestaan zolang andere tabs ze nog importeren; in deze ronde worden ze niet verwijderd.

**Wijzigingen in `ui/tabs/tab_instellingen.py`:**
- Nieuwe `QGroupBox` **"Template"** bovenaan, vóór de bestaande Rapportage- en Import-instellingen-groepen.
  - Label "Actief: `<naam>`"
  - `QComboBox` met alle `themes/*.json`-profielen (ontdekt via `theme.discover_themes()`)
  - Knop "Toepassen" (`objectName = "btnPrimary"`)
  - `QLabel` met info-tekst: *"Wisseling actief na herstart van de app."* — alleen zichtbaar nadat de gebruiker een ander profiel selecteert.
- Bestaande Rapportage- en Import-instellingen-groepen blijven inhoudelijk ongewijzigd; alleen lokale `_BTN_NORMAL`/`_BTN_CLEAR` constanten worden vervangen door `objectName`-toewijzingen aan dezelfde knoppen.

**Wijzigingen in `app/settings.py`:**
- `AppSettings` dataclass krijgt veld `active_theme_name: str = "DKIB"`.

**Wijzigingen in `app/config_manager.py`:**
- Lees/schrijf `active_theme_name` van/naar het config-bestand.

## Bundeled themes

`themes/dkib.json` — schema zoals hierboven, primair `#147ACF`.

`themes/sixgeoconsult.json` — bij implementatie wordt het schema gevuld met de daadwerkelijke kleuren en het lettertype uit `SixGeoConsult_TEMPLATE.xltx` (zelfde extractiemethode als bij DKIB: `openpyxl` + theme-XML inspectie). Pad naar `SIXGeoConsult_logo.jpg` wordt opgenomen onder `assets.app_logo`. Het tweede thema bestaat in deze ronde primair om de discovery + wissel te valideren.

## Tests

`tests/test_theme.py` (alleen pure Python, geen Qt):
- `test_load_valid_json` — laadt `themes/dkib.json` en verifieert kleuren/typografie/geometry/assets.
- `test_load_missing_required_field_raises` — JSON zonder `colors` raised expliciete fout.
- `test_load_missing_optional_assets_ok` — JSON zonder `assets`-key laadt zonder error.
- `test_build_stylesheet_contains_primary_color` — gegenereerde QSS bevat de primaire kleur en de meegegeven font-familienaam.
- `test_discover_themes_finds_json_files` — `discover_themes(themes_dir)` retourneert lijst met namen van alle `*.json`-bestanden.

Het Qt-deel (`theme_apply.py`) heeft geen unit-tests; integratie wordt visueel gevalideerd door de app te starten.

## Qt-valkuilen die we adresseren

1. **Font-naam na registratie** — gebruik `QFontDatabase.applicationFontFamilies(font_id)` om de werkelijke familienaam te krijgen, niet de bestandsnaam. Citeer in QSS met dubbele quotes (`font-family: "Eina 04 Bold"`).
2. **Bootstrap-volgorde** — fonts en stylesheet vóór `MainWindow()` constructie, anders renderen widgets de eerste keer met systeem-default.
3. **QTabBar dubbele lijn op Windows** — combineer `QTabWidget::pane { border-top: 1px solid border; top: -1px; }` met `QTabBar::tab:selected { border-top: 3px solid primary; }`. Visuele test op de doel-Windows 11-machine is verplicht voor commit.
4. **Geen live-switch** — wisseling van thema slaat alleen `active_theme_name` op en toont info-message; bij volgende start is het nieuwe thema actief.
5. **Dropbox-pad niet beschikbaar** — `addApplicationFont` retourneert `-1`; we loggen warning en gaan door met fallback. App moet starten zelfs als de hele Dropbox offline is.

## Buiten scope (deze ronde)

Expliciet niet meegenomen, om scope-creep te voorkomen:

- **De andere 9 tabs** behouden hun lokale `_BTN_PRIMARY`/`_BTN_NORMAL`/`_CARD_STYLE` constanten en blijven werken zoals nu. Migratie per tab gebeurt in vervolgrondes.
- **Matplotlib chart-kleuren** volgen het thema niet. Aparte plan-iteratie nodig (raakt `renderers/`).
- **Word/Excel template-pad-koppeling** — `app_settings.word_template_path` blijft volledig los van het UI-thema. Geen automatische binding.
- **Per-rapport-logo** in TabReportContext blijft ongewijzigd. Het thema-app-logo (linker cornerwidget) en het per-rapport-logo (export-asset) zijn twee aparte concepten.
- **Live theme-switch** zonder herstart. Mogelijke vervolg-iteratie als de need ontstaat.
- **Dark mode of high-contrast varianten** binnen één thema. Geen behoefte uitgesproken.

## Bestanden die deze ronde wijzigen

Toegevoegd:
- `app/theme.py`
- `app/theme_apply.py`
- `themes/dkib.json`
- `themes/sixgeoconsult.json`
- `tests/test_theme.py`

Gewijzigd:
- `run.pyw` — bootstrap-aanroep
- `app/settings.py` — `AppSettings.active_theme_name`
- `app/config_manager.py` — persisteer `active_theme_name`
- `app/main_window.py` — linker cornerwidget met app-logo, `objectName` op export-knop
- `ui/tabs/tab_report_context.py` — verwijder lokale stijlconstanten, voeg `objectName`s toe
- `ui/tabs/tab_instellingen.py` — Template-groep toevoegen, lokale stijlconstanten vervangen door `objectName`s
