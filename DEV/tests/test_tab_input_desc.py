"""Tests voor de invoerbeschrijving-tab."""

from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from reporting.builders.input_description_builder import FaseCard, FaseRow
from ui.tabs.tab_input_desc import TabInputDesc


def test_fasering_intro_gebruikt_projectbrede_fasenamen(qapp) -> None:
    """De app-intro noemt ook fases waarvoor geen fasekaart is geselecteerd."""
    tab = TabInputDesc()
    kaart = FaseCard(fase_num=1, stage_name='Initieel')
    kaart.rows.append(FaseRow('Maaiveld Links', '0,0 [m NAP]'))

    tab.populate_fase_cards(
        [kaart],
        fase_namen=['Initieel', 'Ontgraven', 'Eindsituatie'],
    )

    labels = [label.text() for label in tab.findChildren(QLabel)]
    assert '-  Fase 1: Initieel' in labels
    assert '-  Fase 2: Ontgraven' in labels
    assert '-  Fase 3: Eindsituatie' in labels
