"""QTableWidget voor het tonen van grondlagen per profiel."""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from parsers.models import Project, Stage, SoilProfile
from utils.color_utils import rgb_string_to_tuple


class LayerTableWidget(QWidget):
    """Toont grondlagen van links- en rechtsprofiel in een tabel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel('Geen profiel')
        layout.addWidget(self._label)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(['Nr', 'Materiaal', 'Bov. [m]', 'Ond. [m]', 'Kleur'])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def update_table(
        self,
        project: Project | None,
        stage: Stage | None,
        left_profile: SoilProfile | None,
        right_profile: SoilProfile | None,
    ) -> None:
        """Vul de tabel met laaginformatie.

        Parameters
        ----------
        project:       Huidig project.
        stage:         Actieve bouwfase.
        left_profile:  Linkerprofiel (kan None zijn).
        right_profile: Rechterprofiel (kan None zijn).
        """
        self._table.setRowCount(0)
        if not project or (not left_profile and not right_profile):
            self._label.setText('Geen profiel gevonden.')
            return

        rows: list[tuple] = []
        for side_label, profile in [('L', left_profile), ('R', right_profile)]:
            if not profile:
                continue
            layers = profile.layers
            for i, layer in enumerate(layers):
                bottom = str(layers[i + 1].level) if i + 1 < len(layers) else '...'
                color_str = project.soil_color_map.get(layer.material, 'rgb(220,220,220)')
                rows.append((side_label, layer.nr, layer.material,
                              str(layer.level), bottom, color_str))

        self._table.setRowCount(len(rows))
        self._label.setText(
            f'Links: {left_profile.name if left_profile else "-"}  |  '
            f'Rechts: {right_profile.name if right_profile else "-"}'
        )
        for row_idx, (side, nr, material, top_v, bottom_v, color_str) in enumerate(rows):
            self._table.setItem(row_idx, 0, QTableWidgetItem(f'{side}{nr}'))
            self._table.setItem(row_idx, 1, QTableWidgetItem(material))
            self._table.setItem(row_idx, 2, QTableWidgetItem(top_v))
            self._table.setItem(row_idx, 3, QTableWidgetItem(bottom_v))
            color_item = QTableWidgetItem('')
            try:
                r, g, b = rgb_string_to_tuple(color_str)
                color_item.setBackground(QColor(int(r * 255), int(g * 255), int(b * 255)))
            except Exception:
                pass
            self._table.setItem(row_idx, 4, color_item)
