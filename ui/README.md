# UI-laag

PyQt6-widgets en -dialogen voor het D-Sheet Dashboard. Alle Qt-imports van de
applicatie zijn beperkt tot deze map (en de submap `tabs/`); controllers,
parsers en renderers blijven Qt-vrij.

## Bestanden

| Bestand | Doel |
| --- | --- |
| `info_panel.py` | Informatiekaarten (projectgegevens, elementen, legenda, laagopbouw) als popups en inline-secties. |
| `scale_slider.py` | Slider met instelbare min/max en spinbox-display voor verschaalwaarden. |
| `status_widget.py` | Gekleurde statusbadge (OK / WARN / ERR / idle) met detailregel. |
| `word_pdf_preview_window.py` | Zwevend Word/PDF-previewvenster voor rapportage. |
| `table_styles.py` | Centrale tabelstijl-constanten en stylesheet, gevoed door het actieve thema. |
| `theme_dialog.py` | Dialoog voor het aanmaken, tunen en opslaan van UI-templates. |

## Conventies

- Widgets als instantievariabelen met onderstreep-prefix: `self._badge`,
  `self._table`.
- Constructor delegeert opbouw aan een aparte `_build()`-methode; layouts
  krijgen expliciet `setContentsMargins()` (4-12 px) en `setSpacing()`
  (4-8 px) mee.
- Event-handlers heten `_on_<gebeurtenis>()` en zijn de enige plek die
  signalen omzet in controlleraanroepen.
- Programmatische updates die geen signaalcascade mogen veroorzaken,
  gebeuren tussen `widget.blockSignals(True)` en `widget.blockSignals(False)`.
- Signalen worden als klasseattribuut gedefinieerd
  (`viewport_changed = pyqtSignal(object)`); verbindingen worden
  gecentraliseerd in `main_window.py`.

## Submap

Zie `tabs/` voor de hoofdtabs en sub-tabs van het hoofdvenster (invoer,
resultaten, rapportage, instellingen, debug). Top-level widgets in deze
map worden door die tabs en door `MainWindow` hergebruikt.
