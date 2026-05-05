# Thema's

JSON-thema's die het uiterlijk van de applicatie sturen — kleuren, typografie, geometrie, assets, tabel- en kopstijlen. Bestanden in deze map worden bij opstart automatisch ontdekt door `app.theme.discover_themes()` en toegepast op de `QApplication` via `app.theme_apply.bootstrap_theme()`.

## Bestanden

| Bestand | Doel |
|---|---|
| `dkib.json` | DKIB-huisstijl — primair blauw `#147ACF`, lettertype Eina 04 met fallback Segoe UI. |
| `sixgeoconsult.json` | SIX Geoconsult-huisstijl — eigen kleurenset en typografie. |

## Schema

Elk themabestand is één JSON-object met de volgende top-level keys:

| Key | Inhoud |
|---|---|
| `name` | Weergavenaam (verschijnt in de Instellingen-tab). |
| `colors` | `ThemeColors`: primary, primary_hover, primary_pressed, text, text_muted, border, border_strong, surface, background, ok, warning, danger. |
| `typography` | `ThemeTypography`: family, fallback, size_base, size_title, size_small, size_text, size_table, size_table_header. |
| `geometry` | `ThemeGeometry`: radius, spacing, padding_button. |
| `assets` | `ThemeAssets`: paden naar logo's (relatief aan project-root). |
| `table` | `ThemeTableStyle`: header_bg, header_fg, subheader_bg, subheader_fg, border, row_odd_bg, row_even_bg, label_color, value_color, extra_color. |
| `headings` | `ThemeHeadingStyle`: h1_size/h1_weight/h1_color, h2_size/h2_weight/h2_color. |

Voor de exacte velden en defaults: zie de dataclasses in `app/theme.py`.

## Nieuw thema toevoegen

1. Kopieer een bestaand `.json` (bv. `dkib.json`) naar `themes/<merknaam>.json`.
2. Pas `name`, kleuren, typografie en assets aan.
3. Start de applicatie — `discover_themes()` pakt het bestand automatisch op. Kies het in de Instellingen-tab onder "Thema".

Optioneel kun je via de **Theme-dialoog** (`ui/theme_dialog.py`) interactief een eigen JSON samenstellen en opslaan in deze map.
