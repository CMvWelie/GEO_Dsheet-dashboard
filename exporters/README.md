# Exporters

Serialiseert losse `ReportSection`-lijsten naar Word via `python-docx`. De
exporters zijn de laatste schakel in de rapportage-pipeline: builder,
`ReportSection`, exporter.

## Bestanden

| Bestand | Doel |
|---|---|
| `word_hoofdstuk_exporter.py` | Schrijft een gesorteerde lijst van `ReportSection`-objecten als één damwand-hoofdstuk naar `.docx`. |

## Templates en sidecars

De Word-exporter accepteert een optioneel `template_path`. Zonder sjabloon wordt
een leeg document opgebouwd. Voor het volledige formaat en voorbeelden, zie de
top-level `README.md`; niet hier dupliceren.

## Conventies

- Externe afhankelijkheden (`python-docx`) worden op moduleniveau geïmporteerd.
  Geen lazy `try/except ImportError` in de
  exporters; dependency-checks gebeuren centraal bij app-start in `run.pyw`.
- Foutafhandeling volgt het returntuple-patroon van het project: de publieke
  `export()`-methoden vangen `Exception` breed af en geven `None` terug bij
  succes of een leesbare foutmelding (`str`) bij falen.
- Foutboodschappen, docstrings en commentaar zijn in het Nederlands.
- Geen Qt-imports; deze laag is puur serialisatie en blijft headless.
