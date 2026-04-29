# Templates

Word-templates die door `exporters/word_exporter.py` en `exporters/word_hoofdstuk_exporter.py` als basis worden gebruikt voor rapportage-export. Het pad naar het actieve template wordt ingesteld in de **Rapportage**-tab en bewaard in de gebruikersconfiguratie.

## Bestanden

| Bestand | Doel |
|---|---|
| `damwand_stijlen.docx` | Word-template met paragraafstijlen, kop-niveaus en bookmarks voor damwand-rapportage. |

## Sidecar-mapping

Naast een template kan een JSON-sidecar staan met dezelfde basisnaam plus `.map.json` (bv. `damwand_stijlen.docx.map.json`). De sidecar koppelt rapportage-velden en -secties aan bookmarks in het template.

Het schema en voorbeelden staan in de top-level `README.md` onder *Rapportage en export → Templates*. Zonder sidecar worden alle geselecteerde secties als nieuwe alinea's toegevoegd.

## Nieuw template toevoegen

1. Plaats het `.docx`-bestand in deze map.
2. Optioneel: maak een sidecar `<naam>.docx.map.json` aan met de bookmark-mapping.
3. Open de **Rapportage**-tab en selecteer het nieuwe template via het pad-veld.
