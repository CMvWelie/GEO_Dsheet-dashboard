# Exporters

Serialiseert een `ReportPackage` (en losse `ReportSection`-lijsten) naar Excel
via `openpyxl` en naar Word via `python-docx`. De exporters zijn de laatste
schakel in de rapportage-pipeline: builder, `ReportSection`, exporter.

## Bestanden

| Bestand | Doel |
|---|---|
| `excel_exporter.py` | Schrijft een `ReportPackage` naar `.xlsx`, optioneel via een `.xltx`-sjabloon met sidecar-mapping. |
| `word_exporter.py` | Schrijft een `ReportPackage` naar `.docx`, optioneel via een `.dotx`-sjabloon met bladwijzers en koppen uit de sidecar. |
| `word_hoofdstuk_exporter.py` | Schrijft een gesorteerde lijst van `ReportSection`-objecten als één damwand-hoofdstuk naar `.docx`. |

## Templates en sidecars

Beide hoofd-exporters accepteren een optioneel `template_path`. Naast het
sjabloon wordt een gelijknamige `.map.json` gezocht; deze sidecar koppelt
metadata-sleutels aan cellen of bladwijzers en sectie-id's aan tabbladen of
koppen. Zonder sjabloon wordt een leeg document opgebouwd. Voor het volledige
formaat en voorbeelden, zie de top-level `README.md`; niet hier dupliceren.

## Conventies

- Alle externe afhankelijkheden (`openpyxl`, `python-docx`) worden op
  moduleniveau geïmporteerd. Geen lazy `try/except ImportError` in de
  exporters; dependency-checks gebeuren centraal bij app-start in `run.pyw`.
- Foutafhandeling volgt het returntuple-patroon van het project: de publieke
  `export()`-methoden vangen `Exception` breed af en geven `None` terug bij
  succes of een leesbare foutmelding (`str`) bij falen.
- Foutboodschappen, docstrings en commentaar zijn in het Nederlands.
- Geen Qt-imports; deze laag is puur serialisatie en blijft headless.
