# Hulpfuncties

Gedeelde, framework-onafhankelijke hulpfuncties. Geen Qt-imports, geen state, alleen pure functies of zelfstandige helpers die overal in het project veilig kunnen worden gebruikt.

## Bestanden

| Bestand | Doel |
|---|---|
| `color_utils.py` | Conversie van Windows BGR-integers (zoals D-Sheet ze opslaat) naar `rgb(r, g, b)`-strings via `parse_color_int()`. |
| `geometry.py` | Geometrische hulpfuncties: maaiveldinterpolatie, polygoon-clipping en hoek-/lijnberekeningen voor de renderers. |
| `formatting.py` | Nederlandse getalopmaak: `fmt_number()` met komma als decimaalscheidingsteken en optioneel duizendtal-puntje. |
| `export_manager.py` | PNG- en PDF-export van matplotlib-figuren naar bestand of bytes; gebruikt door PNG-export-knop en Word-export. |

## Belangrijke functies

- `parse_color_int(value: int) -> str` — D-Sheet COLORREF (BGR) → CSS-kleur. Wordt door alle renderers en de grondsoortentabel gebruikt.
- `fmt_number(value: float, decimals: int = 2) -> str` — Nederlandse getalweergave; gebruik deze altijd bij UI- of rapport-output (nooit `f"{x:.2f}"` direct).
- `export_figure_png(fig, path)` / `export_figure_pdf(fig, path)` — schrijven matplotlib-figuren naar disk met consistente DPI/marges.

## Conventies

- Pure functies waar mogelijk; geen verborgen state of singletons.
- Geen Qt-imports — deze module moet headless (zonder `QApplication`) bruikbaar zijn.
- Type hints op alle parameters en returnwaarden; `from __future__ import annotations` bovenaan.
- Foutafhandeling via expliciete returnwaarden of `ValueError`; geen brede `except`-vangst hier.
