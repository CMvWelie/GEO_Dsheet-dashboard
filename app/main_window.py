"""Hoofdvenster van de D-Sheet Dashboard applicatie.

Layout: compacte topbalk + hoofd-tabwidget met 10 tabs.
"""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QGroupBox, QPushButton, QComboBox,
    QCheckBox, QDoubleSpinBox, QScrollArea, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QSizePolicy, QFrame, QAbstractItemView, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _FigureCanvasBase
from matplotlib.figure import Figure


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
from ui.tabs.tab_import import TabImport
from ui.tabs.tab_input_view import TabInputView
from ui.tabs.tab_input_desc import TabInputDesc
from ui.tabs.tab_result_view import TabResultView
from ui.tabs.tab_result_desc import TabResultDesc
from ui.tabs.tab_report_select import TabReportSelect
from ui.tabs.tab_export import TabExport
from ui.tabs.tab_validation import TabValidation
from ui.tabs.tab_instellingen import TabInstellingen
from ui.tabs.tab_grondsoorten import TabGrondsoorten
from ui.preview_window import WordPreviewWindow
from reporting.builders.html_preview_builder import HtmlPreviewBuilder



_CARD_STYLE = (
    'QGroupBox { background: white; border: 1px solid #cfd6dd; border-radius: 8px; '
    'margin-top: 4px; padding: 4px; font-weight: bold; } '
    'QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }'
)
_BTN_PRIMARY = (
    'QPushButton { background: #245b7a; color: white; border: 1px solid #1a4560; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 600; } '
    'QPushButton:hover { background: #1a4560; } '
    'QPushButton:pressed { background: #122f42; border-top: 2px solid #0d2233; }'
)
_BTN_NORMAL = (
    'QPushButton { background: white; color: #2c3e50; border: 1px solid #aabdca; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 500; } '
    'QPushButton:hover { background: #f0f5f9; border-color: #7a9eb0; } '
    'QPushButton:pressed { background: #e4edf3; }'
)
_BTN_DANGER = (
    'QPushButton { background: white; color: #c0392b; border: 1px solid #e08070; '
    'border-radius: 5px; padding: 6px 14px; font-size: 12px; font-weight: 500; } '
    'QPushButton:hover { background: #fdf0ee; border-color: #c0392b; } '
    'QPushButton:pressed { background: #fde0dc; }'
)


def _card(title: str) -> QGroupBox:
    box = QGroupBox(title)
    box.setStyleSheet(_CARD_STYLE)
    return box


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

    def __init__(self):
        super().__init__()
        self.setWindowTitle('D-Sheet Dashboard')
        self.resize(1600, 950)
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)

        self._state = AppState()
        self._controller = AppController(self._state)
        self._report_state = ReportState()
        self._report_controller = ReportController(self._state, self._report_state)

        self._controller.load_config()
        self._preview_window = WordPreviewWindow()
        self._html_builder = HtmlPreviewBuilder()
        self._build_ui()
        self._connect_signals()
        self._tab_instellingen.set_template_path(
            self._state.app_settings.word_template_path
        )
        self._sync_render_spinboxes(self._state.render_settings)
        self._sync_viewport_spinboxes(self._state.viewport_settings)
        self._tab_input_view.update_saved_defaults(
            self._state.render_settings, self._state.viewport_settings
        )
        self._update_all()

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

        # Project-selector als corner-widget van de tab-balk
        self._main_tabs.setCornerWidget(
            self._build_project_corner(), Qt.Corner.TopRightCorner
        )

        # Tab 0: Rapportcontext
        self._tab_report_context = TabReportContext()
        self._main_tabs.addTab(self._tab_report_context, 'Rapportcontext')

        # Tab 1: Import
        self._tab_import = TabImport()
        self._main_tabs.addTab(self._tab_import, 'Import')

        # Tab 2A: Doorsnede
        self._tab_input_view = TabInputView()
        self._info_panel = InfoPanel()
        self._main_tabs.addTab(self._tab_input_view, 'Doorsnede')

        # Tab 2B: Grondsoortentabel
        self._tab_grondsoorten = TabGrondsoorten()
        self._main_tabs.addTab(self._tab_grondsoorten, 'Grondsoortentabel')

        # Tab 2C: Invoerbeschrijving
        self._tab_input_desc = TabInputDesc()
        self._main_tabs.addTab(self._tab_input_desc, 'Invoerbeschrijving')

        # Tab 3A: Resultaten
        self._tab_result_view = TabResultView()
        self._main_tabs.addTab(self._tab_result_view, 'Resultaten')

        # Tab 3B: Resultaatbeschrijving
        self._tab_result_desc = TabResultDesc()
        self._main_tabs.addTab(self._tab_result_desc, 'Resultaatbeschrijving')

        # Tab 4A: Rapportageselectie
        self._tab_report_select = TabReportSelect()
        self._main_tabs.addTab(self._tab_report_select, 'Selectie')

        # Tab 4B: Export (PNG / Excel / Word)
        self._tab_export = TabExport()
        self._main_tabs.addTab(self._tab_export, 'Export')

        # Tab 5: Validatie
        self._tab_validation = TabValidation()
        self._main_tabs.addTab(self._tab_validation, 'Validatie')

        # Tab 6: Instellingen
        self._tab_instellingen = TabInstellingen()
        self._main_tabs.addTab(self._tab_instellingen, 'Instellingen')

        root_layout.addWidget(self._main_tabs, stretch=1)

    def _build_project_corner(self) -> QWidget:
        """Project-selector als corner-widget in de tab-balk."""
        corner = QWidget()
        layout = QHBoxLayout(corner)
        layout.setContentsMargins(4, 2, 8, 2)
        layout.setSpacing(6)
        lbl = QLabel('Project:')
        lbl.setStyleSheet('font-size: 11px; font-weight: 600; color: #2c3e50;')
        layout.addWidget(lbl)
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(160)
        layout.addWidget(self._project_combo)
        return corner

    # ------------------------------------------------------------------
    # Signaalverbindingen
    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self._tab_import.import_btn.clicked.connect(self._on_import)
        self._tab_import.reset_btn.clicked.connect(self._on_reset)
        self._tab_import.project_selected.connect(self._on_list_project_selected)
        self._tab_import.remove_requested.connect(self._on_remove_project)
        self._tab_export.export_png_requested.connect(self._on_export_png)

        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        self._tab_input_view.stage_tabs.currentChanged.connect(self._on_stage_changed)
        self._tab_result_view.output_stage_combo.currentIndexChanged.connect(
            self._on_output_stage_changed)
        self._tab_result_view.result_step_combo.currentIndexChanged.connect(
            self._on_result_step_changed)

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
            iv.uni_scale, iv.norm_scale, iv.hload_low, iv.hload_mid,
            iv.hload_high, iv.mom_radius,
            iv.fs_grondlagen, iv.fs_knikpunten, iv.fs_waterpeil, iv.fs_belastingen,
            iv.fs_constructie, iv.fs_damwand, iv.fs_assen, iv.fs_titel,
        ]:
            sp.valueChanged.connect(self._on_render_change)

        iv.save_defaults_requested.connect(self._on_save_defaults)
        iv.reset_to_factory_requested.connect(self._on_factory_reset)

        # Rapportage-tabs
        self._main_tabs.currentChanged.connect(self._on_main_tab_changed)
        self._tab_export.export_excel_requested.connect(self._on_export_excel)
        self._tab_export.excel_template_changed.connect(
            self._report_controller.set_template_excel)
        self._tab_export.export_word_requested.connect(self._on_export_word)
        self._tab_export.word_template_changed.connect(
            self._report_controller.set_template_word)
        self._tab_validation.validate_requested.connect(self._on_validate)
        self._tab_report_context.metadata_changed.connect(self._on_metadata_changed)
        self._tab_input_desc.override_changed.connect(self._on_override_changed)
        self._tab_report_select.set_plan(self._report_state.plan)
        # Laad huidige metadata in Tab 0
        self._tab_report_context.set_metadata(self._report_state.metadata)
        self._tab_instellingen.template_path_changed.connect(
            self._on_template_path_changed
        )
        self._tab_instellingen.preview_open_requested.connect(
            self._on_preview_open
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_import(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Selecteer D-Sheet bestanden', '',
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
        self._tab_import.refresh_projects(self._state.projects)

    def _on_process(self) -> None:
        if not self._state.raw_files:
            QMessageBox.information(self, 'Geen bestanden', 'Importeer eerst bestanden.')
            return
        try:
            self._parse_files()
        except Exception as exc:
            QMessageBox.critical(self, 'Parseer-fout', str(exc))
            self._tab_import.status_widget.set_status('err', 'Parseer-fout', str(exc))

    def _on_reset(self) -> None:
        self._controller.reset()
        self._tab_import.refresh_projects({})
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.blockSignals(False)
        self._populate_stage_tabs()
        self._tab_result_view.output_stage_combo.clear()
        self._tab_result_view.result_step_combo.clear()
        self._tab_import.status_widget.set_status('idle', 'Gereed', 'Reset voltooid.')
        self._tab_input_view.section_ax.cla()
        self._tab_input_view.section_canvas.draw()
        self._tab_result_view.results_fig.clear()
        self._tab_result_view.results_canvas.draw()
        self._clear_info()

    def _on_project_changed(self, _index: int) -> None:
        key = self._project_combo.currentData()
        if key and key in self._state.projects:
            self._controller.set_active_project(key)
            self._tab_import.select_project(key)
            self._populate_stage_tabs()
            self._populate_output_stage_combo()
            self._populate_result_step_combo()
            self._update_all()

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
            self._tab_import.select_project(self._state.active_project)
            idx = self._project_combo.findData(self._state.active_project)
            if idx >= 0:
                self._project_combo.blockSignals(True)
                self._project_combo.setCurrentIndex(idx)
                self._project_combo.blockSignals(False)
            self._populate_stage_tabs()
            self._populate_output_stage_combo()
            self._populate_result_step_combo()
            self._update_all()
            self._tab_import.status_widget.set_status(
                'ok', 'Project verwijderd', f'"{base_name}" is verwijderd.')
        else:
            self._populate_stage_tabs()
            self._tab_result_view.output_stage_combo.clear()
            self._tab_result_view.result_step_combo.clear()
            self._tab_input_view.section_ax.cla()
            self._tab_input_view.section_canvas.draw()
            self._tab_result_view.results_fig.clear()
            self._tab_result_view.results_canvas.draw()
            self._clear_info()
            self._tab_import.status_widget.set_status(
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
            self._tab_result_view.result_step_combo.currentData() or None)
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
                self._tab_export.set_png_status(f'Fout: {err}', ok=False)
            else:
                self._tab_export.set_png_status(f'Opgeslagen als {path}', ok=True)

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
            hload_low_scale=iv.hload_low.value(),
            hload_mid_scale=iv.hload_mid.value(),
            hload_high_scale=iv.hload_high.value(),
            moment_radius_meters=iv.mom_radius.value(),
            fs_grondlagen=iv.fs_grondlagen.value(),
            fs_knikpunten=iv.fs_knikpunten.value(),
            fs_waterpeil=iv.fs_waterpeil.value(),
            fs_belastingen=iv.fs_belastingen.value(),
            fs_constructie=iv.fs_constructie.value(),
            fs_damwand=iv.fs_damwand.value(),
            fs_assen=iv.fs_assen.value(),
            fs_titel=iv.fs_titel.value(),
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
            (iv.hload_low,       rs.hload_low_scale),
            (iv.hload_mid,       rs.hload_mid_scale),
            (iv.hload_high,      rs.hload_high_scale),
            (iv.mom_radius,      rs.moment_radius_meters),
            (iv.fs_grondlagen,   rs.fs_grondlagen),
            (iv.fs_knikpunten,   rs.fs_knikpunten),
            (iv.fs_waterpeil,    rs.fs_waterpeil),
            (iv.fs_belastingen,  rs.fs_belastingen),
            (iv.fs_constructie,  rs.fs_constructie),
            (iv.fs_damwand,      rs.fs_damwand),
            (iv.fs_assen,        rs.fs_assen),
            (iv.fs_titel,        rs.fs_titel),
        ]
        for sp, val in pairs:
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)

    # ------------------------------------------------------------------
    # Parseren
    # ------------------------------------------------------------------
    def _group_base_name(self, filename: str) -> str:
        return self._controller.group_base_name(filename)

    def _parse_files(self) -> None:
        ok, msg = self._controller.process_files()
        if not ok:
            self._tab_import.status_widget.set_status('err', 'Geen projecten', msg)
            return

        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        for key, proj in self._state.projects.items():
            self._project_combo.addItem(proj.project_name, userData=key)
        self._project_combo.blockSignals(False)

        self._refresh_files_list()
        if self._state.active_project:
            self._tab_import.select_project(self._state.active_project)

        self._populate_stage_tabs()
        self._populate_output_stage_combo()
        self._populate_result_step_combo()
        self._update_all()

        # Vul rapportageplan automatisch met secties van het actieve project
        self._report_controller.auto_populate_plan()
        self._tab_report_select.set_plan(self._report_state.plan)

        self._tab_import.status_widget.set_status('ok', 'Parser gereed', msg)
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
        combo = self._tab_result_view.output_stage_combo
        combo.blockSignals(True)
        combo.clear()
        if project:
            for i, st in enumerate(project.stages):
                combo.addItem(st.name or f'Fase {i + 1}')
        combo.blockSignals(False)

    def _populate_result_step_combo(self) -> None:
        project = self._state.get_active_project()
        combo = self._tab_result_view.result_step_combo
        combo.blockSignals(True)
        combo.clear()
        if project and project.result_steps:
            keys = sorted(project.result_steps.keys(),
                           key=lambda k: self._result_step_sort(k))
            for k in keys:
                label = k.replace('x factor', 'x 1.2')
                combo.addItem(label, userData=k)
            if not self._state.active_result_step:
                default_key = '6.1' if '6.1' in keys else (keys[0] if keys else None)
                self._controller.set_active_result_step(default_key)
            if self._state.active_result_step:
                idx = combo.findData(self._state.active_result_step)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _result_step_sort(self, step: str) -> float:
        return AppController._result_step_sort(step)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _update_all(self) -> None:
        self._update_render_views()
        self._refresh_active_report_tab()
        self._update_preview()

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
        elif active_tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()

    def _render_section(self) -> None:
        ax = self._tab_input_view.section_ax
        canvas = self._tab_input_view.section_canvas
        fig = self._tab_input_view.section_fig
        if not self._state.get_active_project():
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
            self._tab_import.status_widget.set_status('err', 'Renderfout', err)

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
            self._tab_import.status_widget.set_status('warn', 'Resultaatfout', err)

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
        elif tab is self._tab_grondsoorten:
            self._refresh_grondsoorten()

    def _refresh_input_desc(self) -> None:
        cards = self._report_controller.build_all_fase_cards()
        project = self._state.get_active_project()
        if project:
            for card, stage in zip(cards, project.stages):
                card.image_bytes = self._controller.render_stage_png(
                    project, stage, width_px=800, height_px=560)
        self._tab_input_desc.populate_fase_cards(cards)
        damwand_card = self._report_controller.build_damwand_card()
        self._tab_input_desc.populate_damwand_card(damwand_card)

    def _refresh_result_desc(self) -> None:
        """Ververs de resultaatbeschrijving-tab."""
        project = self._state.get_active_project()
        self._tab_result_desc.populate_resultaat_tabel(project)
        secs = self._report_controller.build_result_descriptions()
        self._tab_result_desc.populate(secs)

    def _refresh_grondsoorten(self) -> None:
        """Ververs de grondsoortentabel met het actieve project."""
        project = self._state.get_active_project()
        self._tab_grondsoorten.populate(project)

    def _on_metadata_changed(self) -> None:
        md = self._tab_report_context.get_metadata()
        self._report_state.metadata = md

    def _on_override_changed(self, block_id: str, text: str) -> None:
        self._report_controller.set_text_override(block_id, text)

    def _on_export_excel(self, output_path: str) -> None:
        err = self._report_controller.export_excel(output_path)
        if err:
            self._tab_export.excel_tab.set_status(f'Fout: {err}', ok=False)
        else:
            self._tab_export.excel_tab.set_status(f'Geëxporteerd naar {output_path}', ok=True)

    def _on_export_word(self, output_path: str) -> None:
        err = self._report_controller.export_word(output_path)
        if err:
            self._tab_export.word_tab.set_status(f'Fout: {err}', ok=False)
        else:
            self._tab_export.word_tab.set_status(f'Geëxporteerd naar {output_path}', ok=True)

    def _on_validate(self) -> None:
        issues = self._report_controller.validate()
        self._tab_validation.populate(issues)

    def _on_template_path_changed(self, pad: str) -> None:
        """Sla gewijzigd template-pad op in state en config."""
        self._controller.apply_app_settings(AppSettings(word_template_path=pad))

    def _on_preview_open(self) -> None:
        """Open het preview-venster en render direct."""
        self._preview_window.show()
        self._preview_window.raise_()
        self._update_preview()

    def _update_preview(self) -> None:
        """Herrender de HTML-preview als het venster zichtbaar is."""
        if not self._preview_window.isVisible():
            return
        package = self._report_controller.build_package()
        html = self._html_builder.build(package)
        self._preview_window.set_html(html, len(package.selected_items))
