"""Hoofdvenster van de D-Sheet Dashboard applicatie.

Layout: compacte topbalk + hoofd-tabwidget met 10 tabs.
"""

from __future__ import annotations
import io
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QGroupBox, QPushButton, QComboBox,
    QCheckBox, QDoubleSpinBox, QScrollArea, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QSizePolicy, QFrame, QAbstractItemView, QTabWidget,
    QTableWidget, QApplication,
)
from PyQt6.QtCore import Qt, QThread, QProcess, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _FigureCanvasBase
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from renderers.output_renderer import render_single_result_chart


class FigureCanvas(_FigureCanvasBase):
    """FigureCanvas die muiswiel-events doorstuurt naar de parent (QScrollArea)."""
    def wheelEvent(self, event):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.wheelEvent(event)
                return
            parent = parent.parent()
        super().wheelEvent(event)

from app.state import AppState
from app.settings import RenderSettings, ViewportSettings, AppSettings
from app.controller import AppController
from app.report_state import ReportState
from app.report_controller import ReportController
from ui.info_panel import InfoPanel
from ui.tabs.tab_report_context import TabReportContext
from ui.tabs.tab_input_view import TabInputView
from ui.tabs.tab_input_desc import TabInputDesc
from ui.tabs.tab_result_view import TabResultView
from ui.tabs.tab_result_desc import TabResultDesc
from ui.tabs.tab_report_select import TabReportSelect
from ui.tabs.tab_instellingen import TabInstellingen
from ui.tabs.tab_grondsoorten import TabGrondsoorten
from ui.tabs.tab_grondsoorten_v2 import TabGrondsoortenv2
from ui.tabs.tab_aanvullende_berekeningen import TabAanvullendeBerekeningen
from ui.word_pdf_preview_window import WordPdfPreviewWindow
from app.docx_to_pdf_converter import DocxToPdfConverter
from app.word_preview_worker import WordPreviewWorker
from app import restart_session
from app.theme import BASIC_THEME_NAME, Theme, discover_themes
from app.theme_apply import THEMES_DIR, bootstrap_theme
from reporting.builders.damwand_tekst import project_fase_namen
import ui.table_styles as table_styles


def _spin(lo: float = -9999, hi: float = 9999, val: float = 0, step: float = 0.5,
          decimals: int = 1, width: int = 80) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setValue(val)
    s.setSingleStep(step)
    s.setDecimals(decimals)
    s.setFixedWidth(width)
    return s



class MainWindow(QMainWindow):
    """Hoofdvenster conform de HTML-layout."""

    def __init__(self, thema: Theme | None = None) -> None:
        """Initialiseer het hoofdvenster.

        Parameters
        ----------
        thema:
            Het actieve ``Theme``-object voor branding-elementen (zoals app-logo).
            Mag ``None`` zijn — branding-elementen worden dan weggelaten.
        """
        super().__init__()
        self.setWindowTitle('D-Sheet Dashboard')
        self.resize(1600, 950)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)

        self._theme = thema

        self._state = AppState()
        self._controller = AppController(self._state)
        self._report_state = ReportState()
        self._report_controller = ReportController(self._state, self._report_state)

        self._controller.load_config()
        self._word_pdf_preview_window = WordPdfPreviewWindow()
        self._docx_to_pdf = DocxToPdfConverter()
        self._word_preview_thread: QThread | None = None
        self._word_preview_worker: WordPreviewWorker | None = None

        self._build_ui()

        if self._docx_to_pdf.is_available():
            engines = ', '.join(self._docx_to_pdf.available_engines())
            self._tab_report_select.set_word_pdf_preview_enabled(
                True, f'Beschikbare engines: {engines}'
            )
        else:
            self._tab_report_select.set_word_pdf_preview_enabled(
                False,
                'Geen Word/LibreOffice gevonden — installeer Microsoft Word '
                'of LibreOffice om deze preview te gebruiken.'
            )

        self._connect_signals()
        self._tab_report_select.set_template_path(
            self._state.app_settings.word_template_path
        )
        self._report_controller.set_template_word(
            self._state.app_settings.word_template_path
        )
        self._tab_instellingen.set_import_map(
            self._state.app_settings.standaard_importmap
        )
        # Vul thema-dropdown in Instellingen-tab
        themas = discover_themes(THEMES_DIR)
        actief = self._theme.name if self._theme is not None else self._state.app_settings.active_theme_name
        self._tab_instellingen.set_themes(themas, actief)
        self._tab_result_view.set_breedte(
            self._state.render_settings.resultaat_half_breedte_m * 2
        )
        self._sync_render_spinboxes(self._state.render_settings)
        self._sync_viewport_spinboxes(self._state.viewport_settings)
        self._tab_input_view.update_saved_defaults(
            self._state.render_settings, self._state.viewport_settings
        )
        self._update_all()

        # Herstel paden van een eventuele vorige herstart-actie. Uitgesteld zodat
        # het venster eerst getoond wordt voordat de import start.
        QTimer.singleShot(0, self._herstel_herstart_sessie)

    def _herstel_herstart_sessie(self) -> None:
        """Herlaad bestanden uit een sessiebestand dat bij restart is geschreven."""
        paden = restart_session.pop()
        if not paden:
            return
        bestaand = [p for p in paden if Path(p).exists()]
        if not bestaand:
            return
        self._ingest_paths(bestaand)

    def open_cli_bestanden(self, paths: list[str]) -> None:
        """Laad bestanden die via de commandoregel zijn meegegeven.

        Parameters
        ----------
        paths: Lijst van bestandspaden (.shd/.shi/.shs).
        """
        self._ingest_paths(paths)

    # ------------------------------------------------------------------
    # Drag-and-drop op het hoofdvenster
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        self._ingest_paths(paths)

    # ------------------------------------------------------------------
    # UI opbouw
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(4)

        # ── Hoofd-tabwidget ──────────────────────────────────────────
        self._main_tabs = QTabWidget()
        self._main_tabs.setDocumentMode(False)

        branding = self._build_branding_corner()
        if branding is not None:
            self._main_tabs.setCornerWidget(branding, Qt.Corner.TopLeftCorner)

        # Project-selector als corner-widget van de tab-balk
        self._main_tabs.setCornerWidget(
            self._build_project_corner(), Qt.Corner.TopRightCorner
        )

        # Tab 0: Import (gecombineerd met rapportcontext)
        self._tab_report_context = TabReportContext()
        self._main_tabs.addTab(self._tab_report_context, 'Import')

        # Tab 1: Grondsoortentabel
        self._tab_grondsoorten = TabGrondsoorten()
        self._main_tabs.addTab(self._tab_grondsoorten, 'Grondsoortentabel')

        # Tab 1B: Grondsoortentabel v2
        self._tab_grondsoorten_v2 = TabGrondsoortenv2()
        self._main_tabs.addTab(self._tab_grondsoorten_v2, 'Grondsoortentabel v2')

        # Tab 2: Invoer
        self._tab_input_view = TabInputView()
        self._info_panel = InfoPanel()
        self._main_tabs.addTab(self._tab_input_view, 'Invoer')

        # Tab 2C: Fasering
        self._tab_input_desc = TabInputDesc()
        self._main_tabs.addTab(self._tab_input_desc, 'Fasering')

        # Tab 3A: Uitvoer
        self._tab_result_view = TabResultView()
        self._main_tabs.addTab(self._tab_result_view, 'Uitvoer')

        # Tab 3B: Resultaten
        self._tab_result_desc = TabResultDesc()
        self._main_tabs.addTab(self._tab_result_desc, 'Resultaten')

        # Tab 4A: Aanvullende berekeningen
        self._tab_aanvullende_berekeningen = TabAanvullendeBerekeningen()
        self._main_tabs.addTab(self._tab_aanvullende_berekeningen, 'Aanvullende berekeningen')

        # Tab 4B: Rapport-export
        self._tab_report_select = TabReportSelect()
        self._main_tabs.addTab(self._tab_report_select, 'Rapport-export')

        # Instellingen: verborgen tab, geopend via knop rechtsboven
        self._tab_instellingen = TabInstellingen()
        self._settings_tab_index = self._main_tabs.addTab(self._tab_instellingen, 'Instellingen')
        self._main_tabs.tabBar().setTabVisible(self._settings_tab_index, False)

        root_layout.addWidget(self._main_tabs, stretch=1)

    def _build_branding_corner(self) -> QWidget | None:
        """Logo-cornerwidget linksboven in de tabbalk.

        Returns
        -------
        QWidget | None
            Een QLabel met het thema-app-logo, of ``None`` als er geen logo is
            of als het bestand niet geladen kan worden.
        """
        if self._theme is None or not self._theme.assets.app_logo:
            return None

        logo_path = self._resolve_logo_path(self._theme.assets.app_logo)
        if logo_path is None:
            return None

        from PyQt6.QtGui import QPixmap
        pix = QPixmap(str(logo_path))
        if pix.isNull():
            return None

        pix = pix.scaledToHeight(
            28, Qt.TransformationMode.SmoothTransformation
        )
        label = QLabel()
        label.setPixmap(pix)
        label.setContentsMargins(8, 2, 8, 2)
        return label

    def _resolve_logo_path(self, logo_path: str) -> Path | None:
        """Los logo-paden uit themebestanden op over verschillende gebruikerspaden."""
        pad = Path(logo_path)
        if pad.exists():
            return pad

        parts = pad.parts
        try:
            idx = parts.index('Dropbox')
        except ValueError:
            return None

        dropbox_root = next(
            (parent for parent in Path(__file__).resolve().parents if parent.name == 'Dropbox'),
            None,
        )
        if dropbox_root is None:
            return None
        kandidaat = dropbox_root.joinpath(*parts[idx + 1:])
        if kandidaat.exists():
            return kandidaat
        return None

    def _build_project_corner(self) -> QWidget:
        """Project-selector + instellingenknop als corner-widget in de tab-balk."""
        corner = QWidget()
        corner.setObjectName('tabCornerRight')
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)
        lbl = QLabel('Project:')
        lbl.setObjectName('projectLabel')
        layout.addWidget(lbl)
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(160)
        layout.addWidget(self._project_combo)
        self._btn_instellingen = QPushButton('Instellingen')
        self._btn_instellingen.setObjectName('btnNormal')
        layout.addWidget(self._btn_instellingen)
        return corner

    # ------------------------------------------------------------------
    # Signaalverbindingen
    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self._tab_report_context.import_btn.clicked.connect(self._on_import)
        self._tab_report_context.reset_btn.clicked.connect(self._on_reset)
        self._tab_report_context.project_selected.connect(self._on_list_project_selected)
        self._tab_report_context.remove_requested.connect(self._on_remove_project)
        self._tab_input_view.export_png_requested.connect(self._on_export_png)
        self._tab_input_view.copy_clipboard_requested.connect(self._on_copy_clipboard)
        self._tab_result_view.copy_subplot_requested.connect(self._on_copy_clipboard_uitvoer)
        self._btn_instellingen.clicked.connect(self._on_settings_requested)

        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        self._tab_input_view.stage_tabs.currentChanged.connect(self._on_stage_changed)
        self._tab_result_view.output_stage_tabs.currentChanged.connect(
            self._on_output_stage_changed)
        self._tab_result_view.result_step_tabs.currentChanged.connect(
            self._on_result_step_changed)
        self._tab_result_view.breedte_slider.valueChanged.connect(
            self._on_resultaat_breedte_changed)

        self._tab_input_view.auto_check.toggled.connect(self._on_viewport_change)
        for sp in [self._tab_input_view.xmin_spin, self._tab_input_view.xmax_spin,
                   self._tab_input_view.ymin_spin, self._tab_input_view.ymax_spin]:
            sp.valueChanged.connect(self._on_viewport_change)

        self._tab_input_view.btn_info_meta.clicked.connect(self._info_panel.show_popup_meta)
        self._tab_input_view.btn_info_counts.clicked.connect(self._info_panel.show_popup_counts)
        self._tab_input_view.btn_info_legend.clicked.connect(self._info_panel.show_popup_legend)
        self._tab_input_view.btn_info_layers.clicked.connect(self._info_panel.show_popup_layers)
        self._tab_input_view.btn_info_objects.clicked.connect(self._info_panel.show_popup_objects)
        self._tab_input_view.btn_info_debug.clicked.connect(self._info_panel.show_popup_debug)

        iv = self._tab_input_view
        for sp in [
            iv.uni_scale, iv.norm_scale, iv.hload_scale,
            iv.mom_radius, iv.waterpeil_schaal, iv.maaiveld_schaal,
            iv.fs_grondlagen, iv.fs_knikpunten, iv.fs_waterpeil, iv.fs_belastingen,
            iv.fs_constructie, iv.fs_damwand, iv.fs_assen,
        ]:
            sp.valueChanged.connect(self._on_render_change)

        iv.save_defaults_requested.connect(self._on_save_defaults)
        iv.reset_to_factory_requested.connect(self._on_factory_reset)

        # Rapportage-tabs
        self._main_tabs.currentChanged.connect(self._on_main_tab_changed)
        self._tab_report_select.export_word_requested.connect(self._on_export_word)
        self._tab_report_select.template_path_changed.connect(
            self._on_template_path_changed)
        self._tab_report_select.template_path_changed.connect(
            self._report_controller.set_template_word)
        self._tab_report_context.metadata_changed.connect(self._on_metadata_changed)
        self._tab_input_desc.override_changed.connect(self._on_override_changed)
        self._tab_report_select.set_plan(self._report_state.plan)
        # Laad huidige metadata in Tab 0
        self._tab_report_context.set_metadata(self._report_state.metadata)
        self._tab_instellingen.import_map_changed.connect(
            self._on_import_map_changed
        )
        self._tab_instellingen.theme_selected.connect(self._on_theme_selected)
        self._tab_instellingen.theme_created.connect(self._on_theme_created)
        self._tab_instellingen.theme_updated.connect(self._on_theme_updated)
        self._tab_instellingen.theme_delete_requested.connect(self._on_theme_delete_requested)
        self._tab_instellingen.restart_requested.connect(self._on_restart_app)
        self._tab_report_select.word_pdf_preview_open_requested.connect(
            self._on_word_pdf_preview_open
        )
        self._tab_report_select.selection_changed.connect(
            self._update_word_pdf_preview
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_import(self) -> None:
        startmap = self._state.app_settings.standaard_importmap or ''
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Selecteer D-Sheet bestanden', startmap,
            'D-Sheet bestanden (*.shi *.shd *.shs);;Alle bestanden (*)'
        )
        self._ingest_paths(paths)

    def _ingest_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        ok, msg = self._controller.ingest_paths(paths)
        if not ok:
            QMessageBox.warning(self, 'Leesfouten', msg)
        self._parse_files()

    def _refresh_files_list(self) -> None:
        self._tab_report_context.refresh_projects(self._state.projects)

    def _on_process(self) -> None:
        if not self._state.raw_files:
            QMessageBox.information(self, 'Geen bestanden', 'Importeer eerst bestanden.')
            return
        try:
            self._parse_files()
        except Exception as exc:
            QMessageBox.critical(self, 'Parseer-fout', str(exc))
            self._tab_report_context.status_widget.set_status('err', 'Parseer-fout', str(exc))

    def _on_reset(self) -> None:
        self._controller.reset()
        self._tab_aanvullende_berekeningen.update_project(None)
        self._tab_instellingen.update_project(None)
        self._tab_report_context.refresh_projects({})
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.blockSignals(False)
        self._populate_stage_tabs()
        self._tab_result_view.clear_output_stages()
        self._tab_result_view.clear_result_steps()
        self._tab_report_context.status_widget.set_status('idle', 'Gereed', 'Reset voltooid.')
        self._tab_input_view.section_ax.cla()
        self._tab_input_view.section_canvas.draw()
        self._tab_result_view.results_fig.clear()
        self._tab_result_view.results_canvas.draw()
        self._clear_info()

    def _on_project_changed(self, _index: int) -> None:
        key = self._project_combo.currentData()
        if key and key in self._state.projects:
            self._controller.set_active_project(key)
            self._tab_report_context.select_project(key)
            self._populate_stage_tabs()
            self._populate_output_stage_combo()
            self._populate_result_step_combo()
            self._update_all()
            self._report_controller.auto_populate_plan()
            self._tab_report_select.set_plan(self._report_state.plan)

    def _on_list_project_selected(self, base_name: str) -> None:
        """Gebruiker klikt op project in de importlijst."""
        if base_name not in self._state.projects:
            return
        self._controller.set_active_project(base_name)
        idx = self._project_combo.findData(base_name)
        if idx >= 0:
            self._project_combo.blockSignals(True)
            self._project_combo.setCurrentIndex(idx)
            self._project_combo.blockSignals(False)
        self._populate_stage_tabs()
        self._populate_output_stage_combo()
        self._populate_result_step_combo()
        self._update_all()
        self._report_controller.auto_populate_plan()
        self._tab_report_select.set_plan(self._report_state.plan)

    def _on_remove_project(self, base_name: str) -> None:
        """Verwijder één project inclusief bijbehorende bestanden."""
        self._controller.remove_project(base_name)
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        for key, proj in self._state.projects.items():
            self._project_combo.addItem(proj.project_name, userData=key)
        self._project_combo.blockSignals(False)
        self._refresh_files_list()
        if self._state.active_project:
            self._tab_report_context.select_project(self._state.active_project)
            idx = self._project_combo.findData(self._state.active_project)
            if idx >= 0:
                self._project_combo.blockSignals(True)
                self._project_combo.setCurrentIndex(idx)
                self._project_combo.blockSignals(False)
            self._populate_stage_tabs()
            self._populate_output_stage_combo()
            self._populate_result_step_combo()
            self._update_all()
            self._tab_report_context.status_widget.set_status(
                'ok', 'Project verwijderd', f'"{base_name}" is verwijderd.')
        else:
            self._populate_stage_tabs()
            self._tab_result_view.clear_output_stages()
            self._tab_result_view.clear_result_steps()
            self._tab_input_view.section_ax.cla()
            self._tab_input_view.section_canvas.draw()
            self._tab_result_view.results_fig.clear()
            self._tab_result_view.results_canvas.draw()
            self._clear_info()
            self._tab_report_context.status_widget.set_status(
                'idle', 'Gereed', 'Alle projecten verwijderd.')

    def _on_stage_changed(self, index: int) -> None:
        self._controller.set_active_stage(index)
        self._move_canvas_to_tab(index)
        self._update_all()

    def _on_output_stage_changed(self, index: int) -> None:
        self._controller.set_active_output_stage(index)
        self._render_results()

    def _on_result_step_changed(self, _index: int) -> None:
        self._controller.set_active_result_step(
            self._tab_result_view.current_result_step_key())
        self._render_results()

    def _on_viewport_change(self) -> None:
        if self._tab_input_view.auto_check.isChecked():
            project = self._state.get_active_project()
            if project is not None:
                vp = self._controller.compute_auto_viewport(project)
                self._sync_viewport_spinboxes(vp)
        self._controller.apply_viewport_settings(self._read_viewport())
        self._render_section()

    def _on_render_change(self) -> None:
        self._controller.apply_render_settings(self._read_render())
        self._render_section()

    def _on_save_defaults(self) -> None:
        """Sla huidige instellingen permanent op als standaard."""
        self._controller.save_config()
        iv = self._tab_input_view
        iv.update_saved_defaults(
            self._state.render_settings, self._state.viewport_settings
        )
        # Activeer auto-knoppen zodat sliders vergrendeld zijn op de opgeslagen waarden
        for btn in (iv.auto_check, iv.rs_auto_btn, iv.fs_auto_btn):
            btn.setChecked(True)

    def _on_factory_reset(self) -> None:
        """Herstel fabrieksstandaarden in state en herrender."""
        self._controller.apply_viewport_settings(self._read_viewport())
        self._controller.apply_render_settings(self._read_render())
        self._render_section()

    def _on_export_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, 'Exporteer als PNG', 'dsheet_doorsnede.png',
            'PNG-afbeelding (*.png)'
        )
        if path:
            err = self._controller.export_png(self._tab_input_view.section_fig, path)
            if err:
                QMessageBox.critical(self, 'Export-fout', err)
                self._tab_input_view.set_png_status(f'Fout: {err}', ok=False)
            else:
                self._tab_input_view.set_png_status(f'Opgeslagen als {path}', ok=True)

    def _on_copy_clipboard(self) -> None:
        project = self._state.get_active_project()
        stage_idx = self._tab_input_view.stage_tabs.currentIndex()
        fase = (project.stages[stage_idx].name
                if project and 0 <= stage_idx < len(project.stages) else '')
        fig = self._tab_input_view.section_fig
        suptitle_obj = (fig.suptitle(f'Fase: {fase}', fontsize=10,
                                     color='#444444', ha='center', x=0.5, y=1.0)
                        if fase else None)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        if suptitle_obj:
            suptitle_obj.remove()
        buf.seek(0)
        img = QImage.fromData(buf.read())
        QApplication.clipboard().setPixmap(QPixmap.fromImage(img))
        self._tab_input_view.set_png_status('Gekopieerd naar klembord', ok=True)

    def _on_copy_clipboard_uitvoer(self, idx: int) -> None:
        project = self._state.get_active_project()
        stage_idx = self._tab_result_view.output_stage_tabs.currentIndex()
        fase = (project.stages[stage_idx].name
                if project and 0 <= stage_idx < len(project.stages) else '')
        stap_tabs = self._tab_result_view.result_step_tabs
        stap_raw = stap_tabs.tabText(stap_tabs.currentIndex()) if stap_tabs.count() > 0 else ''
        stap = f'stap {stap_raw.rstrip("- ").strip()}' if stap_raw.strip() else ''
        subtitle = ' - '.join(x for x in (fase, stap) if x) or None

        if idx == -1:
            fig = self._tab_result_view.results_fig
            suptitle_obj = (fig.suptitle(subtitle, fontsize=8, color='#888888',
                                         ha='left', x=0.01, y=1.0)
                            if subtitle else None)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            if suptitle_obj:
                suptitle_obj.remove()
            buf.seek(0)
            img = QImage.fromData(buf.read())
            QApplication.clipboard().setPixmap(QPixmap.fromImage(img))
            return

        if not project:
            return
        active_step = self._tab_result_view.current_result_step_key()
        fig = Figure(figsize=(6, 8), dpi=150)
        FigureCanvasAgg(fig)
        render_single_result_chart(fig, project, stage_idx, idx, active_step,
                                   self._state.render_settings, subtitle)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img = QImage.fromData(buf.read())
        QApplication.clipboard().setPixmap(QPixmap.fromImage(img))

    # ------------------------------------------------------------------
    # Lees UI-waarden
    # ------------------------------------------------------------------
    def _read_viewport(self) -> ViewportSettings:
        iv = self._tab_input_view
        return ViewportSettings(
            auto=iv.auto_check.isChecked(),
            x_min=iv.xmin_spin.value(),
            x_max=iv.xmax_spin.value(),
            y_min=iv.ymin_spin.value(),
            y_max=iv.ymax_spin.value(),
        )

    def _read_render(self) -> RenderSettings:
        iv = self._tab_input_view
        return RenderSettings(
            uniform_meters_per_10kpa=iv.uni_scale.value(),
            normal_meters_per_10knm=iv.norm_scale.value(),
            hload_scale=iv.hload_scale.value(),
            moment_radius_meters=iv.mom_radius.value(),
            waterpeil_schaal=iv.waterpeil_schaal.value(),
            maaiveld_schaal=iv.maaiveld_schaal.value(),
            fs_grondlagen=iv.fs_grondlagen.value(),
            fs_knikpunten=iv.fs_knikpunten.value(),
            fs_waterpeil=iv.fs_waterpeil.value(),
            fs_belastingen=iv.fs_belastingen.value(),
            fs_constructie=iv.fs_constructie.value(),
            fs_damwand=iv.fs_damwand.value(),
            fs_assen=iv.fs_assen.value(),
            resultaat_half_breedte_m=self._tab_result_view.breedte_slider.value() / 2.0,
        )

    def _sync_viewport_spinboxes(self, vp: ViewportSettings) -> None:
        iv = self._tab_input_view
        for sp, val in [(iv.xmin_spin, vp.x_min), (iv.xmax_spin, vp.x_max),
                        (iv.ymin_spin, vp.y_min), (iv.ymax_spin, vp.y_max)]:
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)

    def _sync_render_spinboxes(self, rs: RenderSettings) -> None:
        """Vul render-spinboxen vanuit RenderSettings (zonder signals te triggeren)."""
        iv = self._tab_input_view
        pairs = [
            (iv.uni_scale,       rs.uniform_meters_per_10kpa),
            (iv.norm_scale,      rs.normal_meters_per_10knm),
            (iv.hload_scale,     rs.hload_scale),
            (iv.mom_radius,         rs.moment_radius_meters),
            (iv.waterpeil_schaal,   rs.waterpeil_schaal),
            (iv.maaiveld_schaal,    rs.maaiveld_schaal),
            (iv.fs_grondlagen,      rs.fs_grondlagen),
            (iv.fs_knikpunten,   rs.fs_knikpunten),
            (iv.fs_waterpeil,    rs.fs_waterpeil),
            (iv.fs_belastingen,  rs.fs_belastingen),
            (iv.fs_constructie,  rs.fs_constructie),
            (iv.fs_damwand,      rs.fs_damwand),
            (iv.fs_assen,        rs.fs_assen),
        ]
        for sp, val in pairs:
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)
        self._tab_result_view.set_breedte(rs.resultaat_half_breedte_m * 2)

    # ------------------------------------------------------------------
    # Parseren
    # ------------------------------------------------------------------
    def _group_base_name(self, filename: str) -> str:
        return self._controller.group_base_name(filename)

    def _parse_files(self) -> None:
        ok, msg = self._controller.process_files()
        if not ok:
            self._tab_report_context.status_widget.set_status('err', 'Geen projecten', msg)
            return

        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        for key, proj in self._state.projects.items():
            self._project_combo.addItem(proj.project_name, userData=key)
        self._project_combo.blockSignals(False)

        self._refresh_files_list()
        if self._state.active_project:
            self._tab_report_context.select_project(self._state.active_project)

        self._populate_stage_tabs()
        self._populate_output_stage_combo()
        self._populate_result_step_combo()
        self._update_all()

        # Vul rapportageplan automatisch met secties van het actieve project
        self._report_controller.auto_populate_plan()
        self._tab_report_select.set_plan(self._report_state.plan)

        self._tab_report_context.status_widget.set_status('ok', 'Parser gereed', msg)
        self._controller.save_config()

    def _populate_stage_tabs(self) -> None:
        project = self._state.get_active_project()
        stage_tabs = self._tab_input_view.stage_tabs
        section_canvas = self._tab_input_view.section_canvas
        stage_tabs.blockSignals(True)

        # Ontkoppel canvas van z'n huidige tab-parent zodat het niet mee
        # wordt vernietigd wanneer de tab-widgets worden verwijderd.
        section_canvas.setParent(self)  # type: ignore[arg-type]
        section_canvas.hide()

        # Verwijder alle bestaande tabs
        while stage_tabs.count() > 0:
            w = stage_tabs.widget(0)
            stage_tabs.removeTab(0)
            if w is not None:
                w.setParent(None)  # type: ignore[arg-type]

        stages = (project.stages if project and project.stages
                  else [type('S', (), {'name': 'Standaard'})()])
        for s in stages:
            label = s.name if hasattr(s, 'name') else str(s)
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            stage_tabs.addTab(tab_widget, label)

        # Zet canvas in het eerste tab
        self._move_canvas_to_tab(0)
        stage_tabs.setCurrentIndex(0)
        stage_tabs.blockSignals(False)

    def _move_canvas_to_tab(self, index: int) -> None:
        """Verplaats de gedeelde canvas-widget naar het gewenste tab."""
        stage_tabs = self._tab_input_view.stage_tabs
        section_canvas = self._tab_input_view.section_canvas
        tab_widget = stage_tabs.widget(index)
        if tab_widget is None:
            return
        tab_layout = tab_widget.layout()
        if tab_layout is not None and tab_layout.indexOf(section_canvas) < 0:
            section_canvas.setParent(tab_widget)  # type: ignore[arg-type]
            tab_layout.addWidget(section_canvas)
        section_canvas.show()

    def _populate_output_stage_combo(self) -> None:
        project = self._state.get_active_project()
        if project:
            namen = [st.name or f'Fase {i + 1}' for i, st in enumerate(project.stages)]
            self._tab_result_view.populate_output_stages(namen)
        else:
            self._tab_result_view.clear_output_stages()

    def _populate_result_step_combo(self) -> None:
        project = self._state.get_active_project()
        if project and project.result_steps:
            keys = sorted(project.result_steps.keys(),
                           key=lambda k: self._result_step_sort(k))
            labels = [k.replace('x factor', 'x 1.2') for k in keys]
            if not self._state.active_result_step:
                default_key = '6.1' if '6.1' in keys else (keys[0] if keys else None)
                self._controller.set_active_result_step(default_key)
            self._tab_result_view.populate_result_steps(
                keys, labels, actief=self._state.active_result_step)
        else:
            self._tab_result_view.clear_result_steps()

    def _result_step_sort(self, step: str) -> float:
        return AppController._result_step_sort(step)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _update_all(self) -> None:
        self._update_render_views()
        self._refresh_active_report_tab()
        self._tab_aanvullende_berekeningen.update_project(
            self._state.get_active_project()
        )
        self._tab_instellingen.update_project(
            self._state.get_active_project()
        )

    def _update_render_views(self) -> None:
        project = self._state.get_active_project()
        stage = self._state.get_active_stage()

        vp = self._controller.apply_auto_viewport()
        if vp is not None:
            self._sync_viewport_spinboxes(vp)

        left_p = self._controller.get_stage_profile('left') if project else None
        right_p = self._controller.get_stage_profile('right') if project else None
        self._info_panel.update(project, stage, left_p, right_p)
        self._render_section()
        self._render_results()

    def _refresh_active_report_tab(self) -> None:
        active_tab = self._main_tabs.currentWidget()
        if active_tab is self._tab_input_desc:
            self._refresh_input_desc()
        elif active_tab is self._tab_result_desc:
            self._refresh_result_desc()
        elif active_tab is self._tab_result_view:
            self._refresh_uitvoer_tabellen()
        elif active_tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()
        elif active_tab is self._tab_grondsoorten_v2:
            self._refresh_grondsoorten_v2()

    def _render_section(self) -> None:
        ax = self._tab_input_view.section_ax
        canvas = self._tab_input_view.section_canvas
        fig = self._tab_input_view.section_fig
        project = self._state.get_active_project()
        if not project:
            ax.cla()
            ax.set_facecolor('white')
            ax.text(0.5, 0.5, 'Geen project geladen',
                    transform=ax.transAxes,
                    ha='center', va='center', fontsize=13, color='#888')
            canvas.draw()
            return
        err = self._controller.render_section(ax, fig)
        canvas.draw()
        if err:
            self._tab_report_context.status_widget.set_status('err', 'Renderfout', err)

    def _render_results(self) -> None:
        project = self._state.get_active_project()
        fig = self._tab_result_view.results_fig
        canvas = self._tab_result_view.results_canvas
        if not project or not project.result_steps:
            fig.clear()
            ax = fig.add_subplot(111)
            ax.set_facecolor('white')
            ax.text(0.5, 0.5,
                     'Geen resultaatdata beschikbaar.\nLaad een .shd-bestand met VERIFY STEP-uitvoer.',
                     transform=ax.transAxes, ha='center', va='center',
                     fontsize=11, color='#888888')
            ax.axis('off')
            canvas.draw()
            return
        err = self._controller.render_results(fig)
        canvas.draw()
        if err:
            self._tab_report_context.status_widget.set_status('warn', 'Resultaatfout', err)

    def _clear_info(self) -> None:
        self._info_panel.clear()

    # ------------------------------------------------------------------
    # Rapportage event handlers
    # ------------------------------------------------------------------

    def _on_main_tab_changed(self, index: int) -> None:
        """Ververs rapportagetabs on-demand bij activering."""
        tab = self._main_tabs.widget(index)
        if tab is self._tab_input_desc:
            self._refresh_input_desc()
        elif tab is self._tab_result_desc:
            self._refresh_result_desc()
        elif tab is self._tab_result_view:
            self._refresh_uitvoer_tabellen()
        elif tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()
        elif tab is self._tab_grondsoorten_v2:
            self._refresh_grondsoorten_v2()

    def _refresh_input_desc(self) -> None:
        cards = self._report_controller.build_all_fase_cards()
        project = self._state.get_active_project()
        if project:
            for card, stage in zip(cards, project.stages):
                card.image_bytes = self._controller.render_stage_png(
                    project, stage, width_px=800, height_px=560,
                    toon_titel=False)
        self._tab_input_desc.populate_fase_cards(
            cards,
            project_fase_namen(project),
        )
        damwand_card = self._report_controller.build_damwand_card()
        self._tab_input_desc.populate_damwand_card(damwand_card)

    def _refresh_result_desc(self) -> None:
        """Ververs de resultaatbeschrijving-tab."""
        project = self._state.get_active_project()
        self._tab_result_desc.populate_resultaat_tabel(project)
        secs = self._report_controller.build_result_descriptions()
        self._tab_result_desc.populate(secs)

    def _refresh_uitvoer_tabellen(self) -> None:
        """Ververs de anker- en fase-samenvattingstabellen op de Uitvoer-tab."""
        secs = self._report_controller.build_result_descriptions()
        self._tab_result_view.populate_ondersteuning_tabellen(secs)

    def _refresh_grondsoorten(self) -> None:
        """Ververs de grondsoortentabel met het actieve project."""
        project = self._state.get_active_project()
        self._tab_grondsoorten.populate(project)

    def _refresh_grondsoorten_v2(self) -> None:
        """Ververs de grondsoortentabel v2 met het actieve project."""
        project = self._state.get_active_project()
        self._tab_grondsoorten_v2.populate(project)

    def _on_metadata_changed(self) -> None:
        md = self._tab_report_context.get_metadata()
        self._report_state.metadata = md

    def _on_override_changed(self, block_id: str, text: str) -> None:
        self._report_controller.set_text_override(block_id, text)

    def _on_export_word(self, output_path: str) -> None:
        err = self._report_controller.export_word(output_path)
        if err:
            self._tab_report_select.set_word_status(f'Fout: {err}', ok=False)
        else:
            self._tab_report_select.set_word_status(f'Geëxporteerd naar {output_path}', ok=True)
            os.startfile(output_path)

    def _on_settings_requested(self) -> None:
        """Toon de verborgen Instellingen-pagina."""
        self._main_tabs.setCurrentWidget(self._tab_instellingen)

    def _on_restart_app(self) -> None:
        """Start de applicatie opnieuw op en bewaar de huidige bestandsselectie."""
        restart_session.save(self._state.source_paths)
        QProcess.startDetached(sys.executable, sys.argv)
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_template_path_changed(self, pad: str) -> None:
        """Sla gewijzigd template-pad op in state en config."""
        huidig = self._state.app_settings
        self._controller.apply_app_settings(AppSettings(
            word_template_path=pad,
            standaard_importmap=huidig.standaard_importmap,
            active_theme_name=huidig.active_theme_name,
        ))

    def _on_resultaat_breedte_changed(self, _: int) -> None:
        """Slider voor zichtbare breedte resultaatgrafieken is gewijzigd."""
        self._controller.apply_render_settings(self._read_render())
        self._render_results()

    def _on_import_map_changed(self, pad: str) -> None:
        """Sla gewijzigde standaard importmap op in state en config."""
        huidig = self._state.app_settings
        self._controller.apply_app_settings(AppSettings(
            word_template_path=huidig.word_template_path,
            standaard_importmap=pad,
            active_theme_name=huidig.active_theme_name,
        ))

    def _on_theme_selected(self, naam: str) -> None:
        """Sla nieuw gekozen thema op en pas het direct toe."""
        self._apply_theme(naam)
        actief = self._active_theme_name()
        huidig = self._state.app_settings
        self._controller.apply_app_settings(AppSettings(
            word_template_path=huidig.word_template_path,
            standaard_importmap=huidig.standaard_importmap,
            active_theme_name=actief,
        ))

    def _on_theme_created(self, naam: str) -> None:
        """Laad de theme-dropdown opnieuw en pas het nieuwe template toe."""
        self._tab_instellingen.set_themes(discover_themes(THEMES_DIR), naam)
        self._on_theme_selected(naam)

    def _on_theme_updated(self, naam: str) -> None:
        """Laad de theme-dropdown opnieuw en pas het aangepaste template toe."""
        self._tab_instellingen.set_themes(discover_themes(THEMES_DIR), naam)
        self._on_theme_selected(naam)

    def _on_theme_delete_requested(self, naam: str) -> None:
        """Verwijder een custom themebestand en kies daarna een beschikbare fallback."""
        if naam.lower() in {'dkib', 'sixgeoconsult', BASIC_THEME_NAME.lower()}:
            QMessageBox.warning(self, 'Template verwijderen', 'Deze standaardstijl kan niet worden verwijderd.')
            return

        pad = self._theme_path_for_name(naam)
        if pad is None or not pad.exists():
            QMessageBox.warning(self, 'Template verwijderen', f'Template "{naam}" is niet gevonden.')
            self._tab_instellingen.set_themes(discover_themes(THEMES_DIR), self._active_theme_name())
            return

        try:
            pad.unlink()
        except OSError as exc:
            QMessageBox.warning(self, 'Template verwijderen', f'Verwijderen mislukt:\n{exc}')
            return

        nieuw_actief = self._choose_theme_after_delete(naam)
        self._on_theme_selected(nieuw_actief)

    def _apply_theme(self, naam: str) -> None:
        """Pas een UI-template toe op bestaande widgets en herbouw tabelviews."""
        thema = bootstrap_theme(naam)
        if thema is None:
            QMessageBox.warning(self, 'Template', f'Template "{naam}" kon niet geladen worden.')
            return

        self._theme = thema
        self._refresh_branding_corner()
        for tabel in self.findChildren(QTableWidget):
            if tabel.property('debugTable'):
                tabel.setStyleSheet(table_styles.debug_qtable_style())
            else:
                tabel.setStyleSheet(table_styles.report_qtable_style())

        self._tab_instellingen.set_themes(discover_themes(THEMES_DIR), thema.name)
        self._update_all()

    def _refresh_branding_corner(self) -> None:
        """Werk het logo in de tabbalk bij na een templatewissel."""
        self._main_tabs.setCornerWidget(None, Qt.Corner.TopLeftCorner)
        branding = self._build_branding_corner()
        if branding is not None:
            self._main_tabs.setCornerWidget(branding, Qt.Corner.TopLeftCorner)
            branding.show()

    def _active_theme_name(self) -> str:
        return self._theme.name if self._theme is not None else BASIC_THEME_NAME

    def _theme_path_for_name(self, naam: str):
        for theme_name, pad in discover_themes(THEMES_DIR):
            if theme_name == naam and pad:
                return pad
        return None

    def _choose_theme_after_delete(self, deleted_name: str) -> str:
        if self._active_theme_name() != deleted_name:
            return self._active_theme_name()
        available_names = [name for name, _path in discover_themes(THEMES_DIR)]
        for preferred in ('DKIB', 'SixGeoConsult', BASIC_THEME_NAME):
            if preferred in available_names:
                return preferred
        return available_names[0] if available_names else BASIC_THEME_NAME

    def _on_word_pdf_preview_open(self) -> None:
        """Open het Word-WYSIWYG preview-venster en start een conversie."""
        self._word_pdf_preview_window.show()
        self._word_pdf_preview_window.raise_()
        self._start_word_pdf_conversie()

    def _update_word_pdf_preview(self) -> None:
        """Herrender de Word-WYSIWYG preview als het venster zichtbaar is."""
        if not self._word_pdf_preview_window.isVisible():
            return
        self._start_word_pdf_conversie()

    def _start_word_pdf_conversie(self) -> None:
        """Start een nieuwe export+conversie op een aparte thread.

        Een lopende conversie wordt niet onderbroken; de gebruiker moet
        wachten tot die klaar is voordat een nieuwe start.
        """
        if not self._docx_to_pdf.is_available():
            self._word_pdf_preview_window.set_status(
                'Geen conversie-engine beschikbaar', ok=False
            )
            return
        if self._word_preview_thread is not None and \
                self._word_preview_thread.isRunning():
            return  # negeer; lopende conversie eerst afmaken

        self._word_pdf_preview_window.set_busy(True)

        thread = QThread(self)
        worker = WordPreviewWorker(self._report_controller, self._docx_to_pdf)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_word_pdf_finished)
        worker.failed.connect(self._on_word_pdf_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_word_pdf_thread_finished)

        self._word_preview_thread = thread
        self._word_preview_worker = worker
        thread.start()

    def _on_word_pdf_finished(self, pdf_path: str) -> None:
        """Toon het PDF-resultaat in het preview-venster."""
        self._word_pdf_preview_window.set_pdf(pdf_path)

    def _on_word_pdf_failed(self, message: str) -> None:
        """Toon een foutmelding in het preview-venster."""
        self._word_pdf_preview_window.set_status(message, ok=False)

    def _on_word_pdf_thread_finished(self) -> None:
        """Reset thread-referenties zodat een volgende conversie kan starten."""
        self._word_preview_thread = None
        self._word_preview_worker = None

    def closeEvent(self, event) -> None:
        """Sla venstergeometrie op voor herstel bij volgende start."""
        self._state.app_settings.window_geometry = (
            self.saveGeometry().toBase64().data().decode('ascii')
        )
        self._controller.save_config()
        super().closeEvent(event)
