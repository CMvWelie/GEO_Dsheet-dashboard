# Documentatie

Implementatieplannen en design-specs voor afgeronde en lopende features. De documenten worden gegenereerd via de Superpowers-workflow (brainstorm → spec → plan → execute) en bewaard ter referentie.

## Structuur

| Map | Inhoud |
|---|---|
| `superpowers/specs/` | Design-specs: probleemstelling, ontwerpkeuzes, alternatieven en risico's per feature. |
| `superpowers/plans/` | Implementatieplannen: stap-voor-stap aanpak met checkpoints, afgeleid van de bijbehorende spec. |

## Naamconventie

`YYYY-MM-DD-feature-naam[-design].md`

- Specs eindigen op `-design.md` (bv. `2026-04-29-app-styling-multi-template-design.md`).
- Plannen hebben dezelfde basis maar zonder `-design`-suffix (bv. `2026-04-29-app-styling-multi-template.md`).
- De datum is de aanmaakdatum, niet de afrondingsdatum.

## Recent overzicht

| Datum | Feature |
|---|---|
| 2026-04-29 | App-styling met multi-template thema-systeem |
| 2026-04-28 | Overzichtstabel resultaten |
| 2026-04-23 | Debug-tab |
| 2026-04-21 | Verticaal evenwicht |
| 2026-04-20 | Aanvullende berekeningen (container) |
| 2026-04-17 | UI-architectuur, parser/controller-onderhoudbaarheid, exporter-uitbreidbaarheid, kwaliteit (alleen specs) |
| 2026-04-16 | Damwand-hoofdstuk export |
| 2026-04-14 | Grondsoortentabel selectie/export, grondsoorten + damwand resultaten |
| 2026-04-13 | Word-preview venster |

Voor de volledige lijst: zie de bestandsnamen in `superpowers/plans/` en `superpowers/specs/`.
