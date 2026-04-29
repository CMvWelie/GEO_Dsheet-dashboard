"""InfoPanel — informatiekaarten als popup-vensters.

De vier hoofd-informatiekaarten (Projectgegevens, Elementen actieve fase,
Legenda, Laagopbouw actieve fase) zijn verborgen achter knoppen in het
doorsnede-canvas en worden getoond als niet-modale popup-vensters.
Actieve objecten en Diagnose blijven inline zichtbaar.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QDialog, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from parsers.models import Project, Stage, SoilProfile
from ui.table_styles import REPORT_QTABLE_STYLE
from utils.color_utils import rgb_string_to_tuple

_CARD_STYLE = (
    'QGroupBox { background: white; border: 1px solid #cfd6dd; border-radius: 8px; '
    'margin-top: 4px; padding: 4px; font-weight: bold; } '
    'QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }'
)


def _card(title: str) -> QGroupBox:
    box = QGroupBox(title)
    box.setStyleSheet(_CARD_STYLE)
    return box


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def _make_popup(title: str, parent: QWidget, width: int = 420, height: int = 360) -> QDialog:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setWindowFlags(
        Qt.WindowType.Window |
        Qt.WindowType.WindowCloseButtonHint |
        Qt.WindowType.WindowMinimizeButtonHint
    )
    dlg.resize(width, height)
    return dlg


class InfoPanel(QWidget):
    """Toont informatiekaarten voor het actieve project en fase.

    De vier tegels (Projectgegevens, Elementen actieve fase, Legenda,
    Laagopbouw actieve fase) zijn popup-vensters. Roep show_popup_*()
    aan om ze te tonen.

    Gebruik::

        panel.update(project, stage, left_profile, right_profile)
        panel.clear()
        panel.show_popup_meta()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── Popup: Projectgegevens ──────────────────────────────────
        self._popup_meta = _make_popup('Projectgegevens', self, 380, 300)
        meta_card = _card('Projectgegevens')
        self._meta_layout = QGridLayout(meta_card)
        self._meta_layout.setHorizontalSpacing(8)
        scroll_meta = QScrollArea()
        scroll_meta.setWidgetResizable(True)
        scroll_meta.setFrameShape(QFrame.Shape.NoFrame)
        scroll_meta.setWidget(meta_card)
        pm_layout = QVBoxLayout(self._popup_meta)
        pm_layout.addWidget(scroll_meta)

        # ── Popup: Elementen actieve fase ───────────────────────────
        self._popup_counts = _make_popup('Elementen actieve fase', self, 340, 320)
        count_card = _card('Elementen actieve fase')
        count_vl = QVBoxLayout(count_card)
        self._count_labels: dict[str, QLabel] = {}
        count_rows = [
            ('Grondlagen links',       'layers_left'),
            ('Grondlagen rechts',      'layers_right'),
            ('Waterlijnen',            'water'),
            ('Damwanden',              'walls'),
            ('Fasen',                  'stages'),
            ('Ankers actief',          'anchors'),
            ('Stempels actief',        'struts'),
            ('Veersteunen actief',     'springs'),
            ('Rigide steunen actief',  'rigid'),
            ('Uniform loads actief',   'uniform'),
            ('Surcharge loads actief', 'surcharge'),
        ]
        count_grid = QGridLayout()
        for i, (label, key) in enumerate(count_rows):
            count_grid.addWidget(QLabel(label), i, 0)
            lbl = QLabel('0')
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._count_labels[key] = lbl
            count_grid.addWidget(lbl, i, 1)
        count_vl.addLayout(count_grid)
        scroll_counts = QScrollArea()
        scroll_counts.setWidgetResizable(True)
        scroll_counts.setFrameShape(QFrame.Shape.NoFrame)
        scroll_counts.setWidget(count_card)
        pc_layout = QVBoxLayout(self._popup_counts)
        pc_layout.addWidget(scroll_counts)

        # ── Popup: Legenda ──────────────────────────────────────────
        self._popup_legend = _make_popup('Legenda', self, 300, 400)
        legend_card = _card('Legenda')
        self._legend_layout = QVBoxLayout(legend_card)
        self._legend_layout.addWidget(QLabel('Geen grondsoorten.'))
        scroll_legend = QScrollArea()
        scroll_legend.setWidgetResizable(True)
        scroll_legend.setFrameShape(QFrame.Shape.NoFrame)
        scroll_legend.setWidget(legend_card)
        pl_layout = QVBoxLayout(self._popup_legend)
        pl_layout.addWidget(scroll_legend)

        # ── Popup: Laagopbouw actieve fase ──────────────────────────
        self._popup_layers = _make_popup('Laagopbouw actieve fase', self, 480, 400)
        layers_card = _card('Laagopbouw actieve fase')
        layers_vl = QVBoxLayout(layers_card)
        self._layers_label = QLabel('')
        layers_vl.addWidget(self._layers_label)
        self._layers_table = QTableWidget(0, 5)
        self._layers_table.setHorizontalHeaderLabels(
            ['Nr', 'Materiaal', 'Bov. [m]', 'Ond. [m]', ''])
        self._layers_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self._layers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._layers_table.verticalHeader().setVisible(False)
        self._layers_table.setAlternatingRowColors(True)
        self._layers_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._layers_table.setShowGrid(True)
        self._layers_table.setStyleSheet(REPORT_QTABLE_STYLE)
        layers_vl.addWidget(self._layers_table)
        scroll_layers = QScrollArea()
        scroll_layers.setWidgetResizable(True)
        scroll_layers.setFrameShape(QFrame.Shape.NoFrame)
        scroll_layers.setWidget(layers_card)
        pla_layout = QVBoxLayout(self._popup_layers)
        pla_layout.addWidget(scroll_layers)

        # ── Popup: Actieve objecten ─────────────────────────────────
        self._popup_objects = _make_popup('Actieve objecten', self, 420, 340)
        obj_card = _card('Actieve objecten')
        self._objects_layout = QVBoxLayout(obj_card)
        scroll_objects = QScrollArea()
        scroll_objects.setWidgetResizable(True)
        scroll_objects.setFrameShape(QFrame.Shape.NoFrame)
        scroll_objects.setWidget(obj_card)
        po_layout = QVBoxLayout(self._popup_objects)
        po_layout.addWidget(scroll_objects)

        # ── Popup: Diagnose ─────────────────────────────────────────
        self._popup_debug = _make_popup('Diagnose', self, 460, 320)
        debug_card = _card('Diagnose')
        debug_vl = QVBoxLayout(debug_card)
        self._debug_label = QLabel('')
        self._debug_label.setWordWrap(True)
        self._debug_label.setStyleSheet(
            'font-family:Consolas,monospace;font-size:10px;color:#333;'
        )
        debug_vl.addWidget(self._debug_label)
        scroll_debug = QScrollArea()
        scroll_debug.setWidgetResizable(True)
        scroll_debug.setFrameShape(QFrame.Shape.NoFrame)
        scroll_debug.setWidget(debug_card)
        pd_layout = QVBoxLayout(self._popup_debug)
        pd_layout.addWidget(scroll_debug)

    # ------------------------------------------------------------------
    # Popup-tonen
    # ------------------------------------------------------------------

    def show_popup_meta(self) -> None:
        self._popup_meta.show()
        self._popup_meta.raise_()
        self._popup_meta.activateWindow()

    def show_popup_counts(self) -> None:
        self._popup_counts.show()
        self._popup_counts.raise_()
        self._popup_counts.activateWindow()

    def show_popup_legend(self) -> None:
        self._popup_legend.show()
        self._popup_legend.raise_()
        self._popup_legend.activateWindow()

    def show_popup_layers(self) -> None:
        self._popup_layers.show()
        self._popup_layers.raise_()
        self._popup_layers.activateWindow()

    def show_popup_objects(self) -> None:
        self._popup_objects.show()
        self._popup_objects.raise_()
        self._popup_objects.activateWindow()

    def show_popup_debug(self) -> None:
        self._popup_debug.show()
        self._popup_debug.raise_()
        self._popup_debug.activateWindow()

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def update(
        self,
        project: Project | None,
        stage: Stage | None,
        left_profile: SoilProfile | None = None,
        right_profile: SoilProfile | None = None,
    ) -> None:
        """Ververs alle informatiekaarten met de gegeven project/fase-data."""
        self._update_meta(project, stage)
        self._update_counts(project, stage, left_profile, right_profile)
        self._update_legend(project)
        self._update_layers(project, stage, left_profile, right_profile)
        self._update_objects(project, stage)
        self._update_debug(project, stage, left_profile, right_profile)

    def clear(self) -> None:
        """Wis alle informatiekaarten naar lege begintoestand."""
        self._clear_meta()
        _clear_layout(self._legend_layout)
        _clear_layout(self._objects_layout)
        self._layers_table.setRowCount(0)
        self._layers_label.setText('')
        self._debug_label.setText('')
        for lbl in self._count_labels.values():
            lbl.setText('0')
        self._legend_layout.addWidget(QLabel('Geen grondsoorten.'))

    # ------------------------------------------------------------------
    # Interne update-methoden
    # ------------------------------------------------------------------

    def _clear_meta(self) -> None:
        while self._meta_layout.count():
            item = self._meta_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_meta(self, project: Project | None, stage: Stage | None) -> None:
        self._clear_meta()
        if not project:
            return
        items = [
            ('Project',      project.project_name),
            ('Bestandsset',  project.base_name),
            ('Actieve fase', stage.name if stage else '-'),
            ('.shi',  'ja' if project.file_bundle.shi else 'nee'),
            ('.shd',  'ja' if project.file_bundle.shd else 'nee'),
            ('.shs',  'ja' if project.file_bundle.shs else 'nee'),
            ('Profielen',   str(len(project.profiles))),
            ('Surfaces',    str(len(project.surfaces))),
            ('Waterpeilen', str(len(project.waterlevels))),
            ('Belastingen', str(len(project.uniform_loads) + len(project.surcharge_loads))),
        ]
        for row, (label, value) in enumerate(items):
            lbl = QLabel(f'<b>{label}</b>')
            lbl.setStyleSheet('font-weight:bold;font-size:11px;')
            val = QLabel(value)
            val.setStyleSheet('font-size:11px;')
            self._meta_layout.addWidget(lbl, row, 0)
            self._meta_layout.addWidget(val, row, 1)

    def _update_counts(
        self,
        project: Project | None,
        stage: Stage | None,
        left_profile: SoilProfile | None,
        right_profile: SoilProfile | None,
    ) -> None:
        if not project or not stage:
            for lbl in self._count_labels.values():
                lbl.setText('0')
            return
        self._count_labels['layers_left'].setText(
            str(len(left_profile.layers) if left_profile else 0))
        self._count_labels['layers_right'].setText(
            str(len(right_profile.layers) if right_profile else 0))
        self._count_labels['water'].setText(str(len(project.waterlevels)))
        self._count_labels['walls'].setText(str(len(project.sheet_piling)))
        self._count_labels['stages'].setText(str(len(project.stages)))
        self._count_labels['anchors'].setText(str(len(stage.anchors)))
        self._count_labels['struts'].setText(str(len(stage.struts)))
        self._count_labels['springs'].setText(str(len(stage.spring_supports)))
        self._count_labels['rigid'].setText(str(len(stage.rigid_supports)))
        self._count_labels['uniform'].setText(str(len(stage.uniform_loads)))
        self._count_labels['surcharge'].setText(
            str(len(stage.surcharge_loads_left) + len(stage.surcharge_loads_right)))

    def _update_legend(self, project: Project | None) -> None:
        _clear_layout(self._legend_layout)
        if not project or not project.soils:
            self._legend_layout.addWidget(QLabel('Geen grondsoorten.'))
            return
        for soil in project.soils:
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.setSpacing(6)
            swatch = QLabel()
            swatch.setFixedSize(16, 16)
            try:
                r, g, b = rgb_string_to_tuple(soil.color)
                swatch.setStyleSheet(
                    f'background:rgb({int(r*255)},{int(g*255)},{int(b*255)});'
                    'border:1px solid #888;'
                )
            except Exception:
                swatch.setStyleSheet('background:#ddd;border:1px solid #888;')
            row_l.addWidget(swatch)
            name_lbl = QLabel(soil.name)
            name_lbl.setStyleSheet('font-size:11px;')
            row_l.addWidget(name_lbl)
            row_l.addStretch()
            self._legend_layout.addWidget(row_w)

    def _update_layers(
        self,
        project: Project | None,
        stage: Stage | None,
        left_profile: SoilProfile | None,
        right_profile: SoilProfile | None,
    ) -> None:
        self._layers_table.setRowCount(0)
        if not project or not stage:
            self._layers_label.setText('')
            return
        self._layers_label.setText(
            f'Links: {left_profile.name if left_profile else "-"}  |  '
            f'Rechts: {right_profile.name if right_profile else "-"}'
        )
        rows = []
        for side, profile in [('L', left_profile), ('R', right_profile)]:
            if not profile:
                continue
            for i, layer in enumerate(profile.layers):
                bottom = (str(profile.layers[i + 1].level)
                          if i + 1 < len(profile.layers) else '...')
                color = project.soil_color_map.get(layer.material, 'rgb(220,220,220)')
                rows.append((side, layer.nr, layer.material,
                              str(layer.level), bottom, color))
        self._layers_table.setRowCount(len(rows))
        for row_idx, (side, nr, mat, top_v, bot_v, color) in enumerate(rows):
            self._layers_table.setItem(row_idx, 0, QTableWidgetItem(f'{side}{nr}'))
            self._layers_table.setItem(row_idx, 1, QTableWidgetItem(mat))
            self._layers_table.setItem(row_idx, 2, QTableWidgetItem(top_v))
            self._layers_table.setItem(row_idx, 3, QTableWidgetItem(bot_v))
            color_item = QTableWidgetItem('')
            try:
                r, g, b = rgb_string_to_tuple(color)
                color_item.setBackground(
                    QColor(int(r * 255), int(g * 255), int(b * 255)))
            except Exception:
                pass
            self._layers_table.setItem(row_idx, 4, color_item)

    def _update_objects(self, project: Project | None, stage: Stage | None) -> None:
        _clear_layout(self._objects_layout)
        if not project or not stage:
            self._objects_layout.addWidget(QLabel('Geen fase geselecteerd.'))
            return
        groups = [
            ('Ankers',           stage.anchors),
            ('Stempels',         stage.struts),
            ('Veersteunen',      stage.spring_supports),
            ('Rigide steunen',   stage.rigid_supports),
            ('Uniform loads',    stage.uniform_loads),
            ('Surcharge links',  stage.surcharge_loads_left),
            ('Surcharge rechts', stage.surcharge_loads_right),
            ('H-lijnlasten',     stage.horizontal_line_loads),
            ('Momenten',         stage.moments),
            ('Normaalkrachten',  stage.normal_forces),
        ]
        for label, items in groups:
            text = f'<b>{label}:</b> ' + (', '.join(items) if items else '<i>geen</i>')
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet('font-size:11px;')
            self._objects_layout.addWidget(lbl)

    def _update_debug(
        self,
        project: Project | None,
        stage: Stage | None,
        left_profile: SoilProfile | None,
        right_profile: SoilProfile | None,
    ) -> None:
        if not project or not stage:
            self._debug_label.setText('')
            return
        lines = [
            f'Project: {project.project_name}',
            f'Fase: {stage.name}',
            f'Left surface: {stage.left_surface or "-"}',
            f'Right surface: {stage.right_surface or "-"}',
            f'Left water: {stage.left_water or "-"}',
            f'Right water: {stage.right_water or "-"}',
            f'Left profile asked: {stage.left_profile or "-"}',
            f'Right profile asked: {stage.right_profile or "-"}',
            f'Left profile resolved: {left_profile.name if left_profile else "-"}'
            f' @ x={left_profile.x if left_profile else "-"}',
            f'Right profile resolved: {right_profile.name if right_profile else "-"}'
            f' @ x={right_profile.x if right_profile else "-"}',
            f'Surfaces: {", ".join(s.name for s in project.surfaces) or "-"}',
            f'Waterlevels: {", ".join(f"{w.name}={w.level}" for w in project.waterlevels) or "-"}',
        ]
        self._debug_label.setText('\n'.join(lines))
