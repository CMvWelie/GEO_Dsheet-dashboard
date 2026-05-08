"""Tab 2A — Invoerweergave: damwand-doorsnede canvas per fase."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QSizePolicy, QTabWidget,
    QScrollArea, QLabel, QFrame, QDialog, QDoubleSpinBox, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics

from ui.scale_slider import ScaleSlider
from app.settings import RenderSettings, ViewportSettings

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as _FigureCanvasBase
from matplotlib.figure import Figure


class FigureCanvas(_FigureCanvasBase):
    """FigureCanvas die muiswiel-events doorstuurt naar de parent (QScrollArea)."""

    copy_requested = pyqtSignal()

    def wheelEvent(self, event):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.wheelEvent(event)
                return
            parent = parent.parent()
        super().wheelEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act = menu.addAction('Kopieer doorsnede')
        if menu.exec(event.globalPos()) == act:
            self.copy_requested.emit()


def _hsep() -> QFrame:
    """Horizontale scheidingslijn."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet('color: #cfd6dd;')
    return line


def _section_header(title: str, auto_btn: QPushButton) -> QHBoxLayout:
    """Sectie-header: vetgedrukte titel links, Auto-knop rechts."""
    row = QHBoxLayout()
    row.setContentsMargins(0, 4, 0, 2)
    lbl = QLabel(f'<b>{title}</b>')
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(auto_btn)
    return row


class TabInputView(QWidget):
    """Doorsnede-canvas tab (Tab 2A).

    Exposeert attributen die MainWindow hergebruikt:
        stage_tabs, section_fig, section_ax, section_canvas,
        auto_check, xmin_spin, xmax_spin, ymin_spin, ymax_spin,
        uni_scale, norm_scale, hload_scale, mom_radius,
        fs_grondlagen, fs_knikpunten, fs_waterpeil, fs_belastingen,
        fs_constructie, fs_damwand, fs_assen
    """

    save_defaults_requested = pyqtSignal()
    reset_to_factory_requested = pyqtSignal()
    export_png_requested = pyqtSignal()
    copy_clipboard_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._saved_defaults: dict[str, float] = {}  # gevuld na config-load/save
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        # ── Maak alle sliders en auto-knoppen aan ────────────────────

        # Grafiekbereik — 4 losse invoervelden (geen sliders)
        self.auto_check = QPushButton('Auto')
        self.auto_check.setCheckable(True)
        self.auto_check.setChecked(True)
        self.auto_check.setFixedSize(48, 20)
        self.auto_check.setObjectName('btnToggle')

        _VP_SPIN_STYLE = (
            'QDoubleSpinBox { font-size: 11px; color: #245b7a; '
            'background: #f0f5f9; border: 1px solid #aabdca; border-radius: 3px; padding: 2px 4px; }'
            'QDoubleSpinBox:focus { border-color: #245b7a; background: #ffffff; }'
            'QDoubleSpinBox:disabled { color: #aab0b8; background: #eef0f3; '
            'border-color: #d8dce0; }'
        )
        for attr, default in [
            ('xmin_spin', -10.0), ('xmax_spin', 10.0),
            ('ymin_spin', -10.0), ('ymax_spin',  5.0),
        ]:
            sp = QDoubleSpinBox()
            sp.setRange(-200.0, 200.0)
            sp.setValue(default)
            sp.setDecimals(1)
            sp.setSingleStep(0.5)
            sp.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            sp.setFixedWidth(72)
            sp.setStyleSheet(_VP_SPIN_STYLE)
            setattr(self, attr, sp)

        # Verschaling
        self.rs_auto_btn = QPushButton('Auto')
        self.rs_auto_btn.setCheckable(True)
        self.rs_auto_btn.setChecked(True)
        self.rs_auto_btn.setFixedSize(48, 20)
        self.rs_auto_btn.setObjectName('btnToggle')

        self._rs_sliders: list[tuple[str, float]] = []
        for lbl, attr, lo, hi, default in [
            ('Unif. [m/10kPa]', 'uni_scale',   0.1,  5.0,  0.5),
            ('Norm. [m/10kN]',  'norm_scale',  0.1,  5.0,  0.5),
            ('H-last schaal',   'hload_scale', 0.1, 10.0,  2.0),
            ('Momentradius',    'mom_radius',       0.1, 10.0,  1.0),
            ('Waterpeil schaal', 'waterpeil_schaal', 0.2,  5.0,  1.0),
            ('Maaiveld schaal',  'maaiveld_schaal',  0.2,  5.0,  1.0),
        ]:
            setattr(self, attr, ScaleSlider(lbl, lo, hi, default))
            self._rs_sliders.append((attr, default))

        # Tekstgrootte
        self.fs_auto_btn = QPushButton('Auto')
        self.fs_auto_btn.setCheckable(True)
        self.fs_auto_btn.setChecked(True)
        self.fs_auto_btn.setFixedSize(48, 20)
        self.fs_auto_btn.setObjectName('btnToggle')

        self._fs_sliders: list[tuple[str, float]] = []
        for lbl, attr, lo, hi, default in [
            ('Grondlagen',  'fs_grondlagen',  6.0, 20.0,  9.0),
            ('Knikpunten',  'fs_knikpunten',  6.0, 20.0,  7.5),
            ('Waterpeil',   'fs_waterpeil',   6.0, 20.0,  8.0),
            ('Belastingen', 'fs_belastingen', 6.0, 20.0,  8.5),
            ('Constructie', 'fs_constructie', 6.0, 20.0,  8.5),
            ('Damwand',     'fs_damwand',     6.0, 20.0,  8.5),
            ('Assen',       'fs_assen',       6.0, 20.0, 10.0),
        ]:
            setattr(self, attr, ScaleSlider(lbl, lo, hi, default))
            self._fs_sliders.append((attr, default))

        # Verbind auto-knoppen
        self.auto_check.toggled.connect(self._on_vp_auto_toggled)
        self.rs_auto_btn.toggled.connect(self._on_rs_auto_toggled)
        self.fs_auto_btn.toggled.connect(self._on_fs_auto_toggled)

        # Initiële vergrendeling
        self._on_vp_auto_toggled(True)
        self._on_rs_auto_toggled(True)
        self._on_fs_auto_toggled(True)

        # ── Bouw settings-popup ──────────────────────────────────────
        self._settings_popup = self._build_settings_popup()

        # ── Canvas + knoppenbalk ─────────────────────────────────────
        self.stage_tabs = QTabWidget()
        self.stage_tabs.setDocumentMode(True)
        self.stage_tabs.setTabsClosable(False)
        self.stage_tabs.setMovable(False)

        self.section_fig = Figure(figsize=(14, 11), dpi=96)
        self.section_ax = self.section_fig.add_subplot(111)
        self.section_canvas = FigureCanvas(self.section_fig)
        self.section_canvas.copy_requested.connect(self.copy_clipboard_requested)
        self.section_canvas.setMinimumHeight(300)
        self.section_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        _placeholder = QWidget()
        _ph_layout = QVBoxLayout(_placeholder)
        _ph_layout.setContentsMargins(0, 0, 0, 0)
        _ph_layout.addWidget(self.section_canvas)
        self.stage_tabs.addTab(_placeholder, 'Geen fase')

        # Kader om het grafische venster
        canvas_frame = QFrame()
        canvas_frame.setFrameShape(QFrame.Shape.Box)
        canvas_frame.setLineWidth(1)
        canvas_frame.setStyleSheet(
            'QFrame { border: 2px solid #aabdca; border-radius: 4px; background: white; }'
        )
        frame_layout = QVBoxLayout(canvas_frame)
        frame_layout.setContentsMargins(2, 2, 2, 2)
        frame_layout.setSpacing(0)

        frame_layout.addWidget(self.stage_tabs)

        canvas_row = QWidget()
        canvas_row_layout = QHBoxLayout(canvas_row)
        canvas_row_layout.setContentsMargins(0, 0, 0, 0)
        canvas_row_layout.setSpacing(4)
        canvas_row_layout.addWidget(canvas_frame, stretch=1)

        # Knoppenbalk rechts
        btn_strip = QWidget()
        btn_strip.setFixedWidth(138)
        btn_strip_layout = QVBoxLayout(btn_strip)
        btn_strip_layout.setContentsMargins(0, 4, 0, 4)
        btn_strip_layout.setSpacing(6)

        # Tandwielknop bovenaan
        self.btn_settings = QPushButton('⚙ Instellingen')
        self.btn_settings.setObjectName('btnTool')
        self.btn_settings.setFixedHeight(44)
        self.btn_settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_settings.clicked.connect(self._show_settings_popup)
        btn_strip_layout.addWidget(self.btn_settings)

        self.btn_export_png = QPushButton('PNG export')
        self.btn_export_png.setObjectName('btnPrimary')
        self.btn_export_png.setFixedHeight(44)
        self.btn_export_png.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_export_png.clicked.connect(self.export_png_requested)
        btn_strip_layout.addWidget(self.btn_export_png)

        self._png_status = QLabel('')
        self._png_status.setWordWrap(True)
        self._png_status.setObjectName('hintLabel')
        btn_strip_layout.addWidget(self._png_status)

        # Scheidingslijn
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('color: #cfd6dd;')
        btn_strip_layout.addWidget(sep)

        # Info-knoppen
        for label, attr in [
            ('Projectgegevens',  'btn_info_meta'),
            ('Elementen',        'btn_info_counts'),
            ('Legenda',          'btn_info_legend'),
            ('Laagopbouw',       'btn_info_layers'),
            ('Actieve objecten', 'btn_info_objects'),
            ('Diagnose',         'btn_info_debug'),
        ]:
            btn = QPushButton(label)
            btn.setObjectName('btnTool')
            btn.setFixedHeight(44)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            setattr(self, attr, btn)
            btn_strip_layout.addWidget(btn)

        btn_strip_layout.addStretch()
        canvas_row_layout.addWidget(btn_strip)

        root.addWidget(canvas_row, stretch=1)

    def _build_settings_popup(self) -> QDialog:
        """Bouw de weergave-instellingen popup met drie secties in grid-layout."""
        dlg = QDialog(self)
        dlg.setWindowTitle('Weergave-instellingen')
        dlg.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(int(screen.width() * 0.50), 800)
        h = min(int(screen.height() * 0.75), 700)
        dlg.resize(w, h)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(14, 10, 14, 14)
        vbox.setSpacing(6)

        rs_labels = [
            ('uni_scale',   'Uniforme last [m / 10 kPa]'),
            ('norm_scale',  'Normaalkracht [m / 10 kN]'),
            ('hload_scale', 'Horizontale last schaal [m]'),
            ('mom_radius',        'Momentradius [m]'),
            ('waterpeil_schaal',  'Waterpeil symbool schaal'),
            ('maaiveld_schaal',   'Maaiveld symbool schaal'),
        ]
        fs_labels = [
            ('fs_grondlagen',  'Grondlagen'),
            ('fs_knikpunten',  'Knikpunten'),
            ('fs_waterpeil',   'Waterpeil'),
            ('fs_belastingen', 'Belastingen'),
            ('fs_constructie', 'Constructie'),
            ('fs_damwand',     'Damwand'),
            ('fs_assen',       'Assen'),
        ]

        sections = [
            ('Verschaling',   self.rs_auto_btn, rs_labels),
            ('Tekstgrootte',  self.fs_auto_btn, fs_labels),
        ]

        # ── Grafiekbereik: 2×2 spinbox-grid ────────────────────────────
        vbox.addLayout(_section_header('Grafiekbereik', self.auto_check))
        vp_grid = QGridLayout()
        vp_grid.setContentsMargins(0, 4, 0, 4)
        vp_grid.setHorizontalSpacing(12)
        vp_grid.setVerticalSpacing(6)
        for row, col, label, attr in [
            (0, 0, 'X minimum', 'xmin_spin'),
            (0, 2, 'X maximum', 'xmax_spin'),
            (1, 0, 'Y minimum', 'ymin_spin'),
            (1, 2, 'Y maximum', 'ymax_spin'),
        ]:
            lbl = QLabel(label)
            vp_grid.addWidget(lbl, row, col)
            vp_grid.addWidget(getattr(self, attr), row, col + 1)
        vbox.addLayout(vp_grid)
        vbox.addWidget(_hsep())

        # Bereken de breedte van de langste label over de overige secties
        lbl_font = QFont()
        lbl_font.setPointSize(9)
        fm = QFontMetrics(lbl_font)
        all_names = [name for _, _, items in sections for _, name in items]
        label_col_w = max(fm.horizontalAdvance(n) for n in all_names) + 16

        for title, auto_btn, items in sections:
            vbox.addLayout(_section_header(title, auto_btn))

            grid = QGridLayout()
            grid.setContentsMargins(0, 2, 0, 4)
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(1)
            grid.setColumnMinimumWidth(0, label_col_w)
            grid.setColumnStretch(0, 0)
            grid.setColumnStretch(1, 1)

            for row, (attr, full_name) in enumerate(items):
                slider: ScaleSlider = getattr(self, attr)
                slider.set_label_visible(False)
                slider.set_header_visible(row == 0)
                slider.layout().setContentsMargins(4, 1, 4, 1)

                lbl = QLabel(full_name)
                lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                grid.addWidget(lbl, row, 0)
                grid.addWidget(slider, row, 1)

            vbox.addLayout(grid)
            vbox.addWidget(_hsep())

        vbox.addStretch()
        scroll.setWidget(content)

        # ── Knoprij onderaan ────────────────────────────────────────────
        btn_row = QWidget()
        btn_row.setStyleSheet('background: #f5f7f9; border-top: 1px solid #cfd6dd;')
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(12, 8, 12, 8)
        btn_layout.setSpacing(8)

        btn_factory = QPushButton('Reset naar fabrieksinstellingen')
        btn_factory.setObjectName('btnWarning')
        btn_factory.clicked.connect(self._on_factory_reset_clicked)

        btn_save = QPushButton('Opslaan als standaard')
        btn_save.setObjectName('btnPrimary')
        btn_save.clicked.connect(self.save_defaults_requested.emit)

        btn_layout.addWidget(btn_factory)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll, stretch=1)
        outer.addWidget(btn_row)
        return dlg

    # ------------------------------------------------------------------
    # Factory reset
    # ------------------------------------------------------------------

    def _on_factory_reset_clicked(self) -> None:
        """Zet alle sliders terug naar de fabrieksinstellingen."""
        for group in (self._rs_sliders, self._fs_sliders):
            for attr, factory_default in group:
                slider: ScaleSlider = getattr(self, attr)
                slider.blockSignals(True)
                slider.setValue(factory_default)
                slider.setEnabled(False)
                slider.blockSignals(False)

        # Zet auto-knoppen terug op ingeschakeld
        for btn in (self.auto_check, self.rs_auto_btn, self.fs_auto_btn):
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

        # Stel buitenwereld op de hoogte
        self.reset_to_factory_requested.emit()

    # ------------------------------------------------------------------
    # Popup tonen
    # ------------------------------------------------------------------

    def _show_settings_popup(self) -> None:
        self._settings_popup.show()
        self._settings_popup.raise_()
        self._settings_popup.activateWindow()

    # ------------------------------------------------------------------
    # Auto-handlers
    # ------------------------------------------------------------------

    def _on_vp_auto_toggled(self, checked: bool) -> None:
        for attr in ('xmin_spin', 'xmax_spin', 'ymin_spin', 'ymax_spin'):
            getattr(self, attr).setEnabled(not checked)

    def _on_rs_auto_toggled(self, checked: bool) -> None:
        for attr, factory_default in self._rs_sliders:
            slider: ScaleSlider = getattr(self, attr)
            if checked:
                val = self._saved_defaults.get(attr, factory_default)
                slider.blockSignals(True)
                slider.setValue(val)
                slider.blockSignals(False)
            slider.setEnabled(not checked)

    def _on_fs_auto_toggled(self, checked: bool) -> None:
        for attr, factory_default in self._fs_sliders:
            slider: ScaleSlider = getattr(self, attr)
            if checked:
                val = self._saved_defaults.get(attr, factory_default)
                slider.blockSignals(True)
                slider.setValue(val)
                slider.blockSignals(False)
            slider.setEnabled(not checked)

    def update_saved_defaults(self, rs: RenderSettings, vp: ViewportSettings) -> None:
        """Sla de opgeslagen waarden op als terugval voor de auto-knoppen."""
        self._saved_defaults = {
            'uni_scale':      rs.uniform_meters_per_10kpa,
            'norm_scale':     rs.normal_meters_per_10knm,
            'hload_scale':    rs.hload_scale,
            'mom_radius':        rs.moment_radius_meters,
            'waterpeil_schaal':  rs.waterpeil_schaal,
            'maaiveld_schaal':   rs.maaiveld_schaal,
            'fs_grondlagen':  rs.fs_grondlagen,
            'fs_knikpunten':  rs.fs_knikpunten,
            'fs_waterpeil':   rs.fs_waterpeil,
            'fs_belastingen': rs.fs_belastingen,
            'fs_constructie': rs.fs_constructie,
            'fs_damwand':     rs.fs_damwand,
            'fs_assen':       rs.fs_assen,
        }

    def set_png_status(self, text: str, ok: bool = True) -> None:
        color = '#2f7d32' if ok else '#b42318'
        self._png_status.setStyleSheet(f'color:{color};font-size:11px;')
        self._png_status.setText(text)
