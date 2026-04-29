# Hoofd- en subtabs

Elke tab is een onafhankelijke `QWidget`-subklasse die door `app/main_window.py` wordt geïnstantieerd en via `_main_tabs.addTab()` aan de hoofd-tabbalk wordt gehangen. Sommige tabs zijn containers met eigen subtabs (Debug, Aanvullende berekeningen).

## Hoofdtabs

In de volgorde waarin ze in het hoofdvenster verschijnen:

| Bestand | Klasse | Label | Doel |
|---|---|---|---|
| `tab_report_context.py` | `TabReportContext` | Rapportcontext | Bestandsimport, projectkeuze en rapportmetadata (opdrachtgever, auteur, datum, revisie) gecombineerd. |
| `tab_debug.py` | `TabDebug` | Debug | Container met subtabs voor inspectie van geparste invoer- en uitvoerdata. |
| `tab_input_view.py` | `TabInputView` | Doorsnede | Matplotlib-visualisatie van damwand, grondlagen, waterpeilen, ankers, stempels en belastingen per fase. |
| `tab_grondsoorten.py` | `TabGrondsoorten` | Grondsoortentabel | Tabeloverzicht van grondsoorten met selectie- en exportknoppen. |
| `tab_input_desc.py` | `TabInputDesc` | Invoerbeschrijving | Gestructureerde tekstbeschrijving van invoerdata met override-mogelijkheid per blok. |
| `tab_result_view.py` | `TabResultView` | Resultaten | Matplotlib-grafieken van moment, dwarskracht en verplaatsing per VERIFY STEP en fase. |
| `tab_result_desc.py` | `TabResultDesc` | Resultaatbeschrijving | Gestructureerde tekstbeschrijving van rekenresultaten met overrides. |
| `tab_aanvullende_berekeningen.py` | `TabAanvullendeBerekeningen` | Aanvullende berekeningen | Container met subtabs voor extra geotechnische controles. |
| `tab_report_select.py` | `TabReportSelect` | Rapportage | Itemselectie, sortering, Word-templatepad en export-knoppen voor `.docx`/`.xlsx`. |
| `tab_instellingen.py` | `TabInstellingen` | Instellingen | Render-, viewport- en thema-instellingen. Tab is verborgen en wordt geopend via een knop rechtsboven. |

## Subtabs

| Bestand | Klasse | Container | Doel |
|---|---|---|---|
| `tab_debug_invoer.py` | `TabDebugInvoer` | Debug | Boom-/tabelinspectie van het ruwe `Project`-domeinmodel. |
| `tab_debug_uitvoer.py` | `TabDebugUitvoer` | Debug | Inspectie van per-fase uitvoerdata (VERIFY STEPs, intern). |
| `tab_hydraulische_grondbreuk.py` | `TabHydraulischeGrondbreuk` | Aanvullende berekeningen | Toetsing van hydraulische grondbreuk (opbarsten/heave). |
| `tab_verticaal_evenwicht.py` | `TabVerticaalEvenwicht` | Aanvullende berekeningen | Toetsing van verticaal evenwicht inclusief renderer-figuur. |

## Conventies

- Constructorsignatuur: `def __init__(self, parent: QWidget | None = None) -> None:`
- UI-opbouw in `_build()` aan het einde van `__init__`; nooit inline in `__init__`.
- Widgets als `self._<naam>` (private attribuut).
- Signals als klasseattribuut: `metadata_changed = pyqtSignal(dict)`.
- Verbindingen worden centraal gemaakt in `MainWindow._connect_signals()`.
- Tab-inhoud wordt on-demand vernieuwd via `_on_main_tab_changed()` in `MainWindow`.
- Geen directe state-mutaties — alle wijzigingen lopen via `AppController` of `ReportController`.

## Nieuwe tab toevoegen

1. Maak `tab_<naam>.py` met een `QWidget`-subklasse en een `_build()`-methode.
2. Instantieer in `MainWindow._build_ui()` en voeg toe via `self._main_tabs.addTab(...)`.
3. Verbind signals in `MainWindow._connect_signals()`.
4. Voeg eventuele on-demand refresh toe in `_on_main_tab_changed()`.
