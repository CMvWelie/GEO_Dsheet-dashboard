"""Tests voor hydraulische grondbreuk berekeningslogica."""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.tabs.tab_hydraulische_grondbreuk import (
    bereken_hydraulische_grondbreuk,
    extraheer_auto_waarden,
)
from parsers.models import Project, FileBundle, SheetPilingElement, WaterLevel, Soil


def _maak_project(
    inheiniveau: float = -1.0,
    grondwaterstand: float = 8.0,
    grondgewicht: float = 19.0,
) -> Project:
    damwand = SheetPilingElement(
        name='AZ18', x=0.0, bottom=inheiniveau, top=1.0, width=0.9
    )
    waterpeil = WaterLevel(name='NAP+8', level=grondwaterstand)
    grond = Soil(
        name='Zand', color='rgb(255,220,100)', color_int=None,
        gamma_wet=grondgewicht,
    )
    return Project(
        base_name='test', project_name='Testproject',
        file_bundle=FileBundle(),
        sheet_piling=[damwand],
        waterlevels=[waterpeil],
        soils=[grond],
    )


def test_berekening_voldoet_niet():
    """Rekenvoorbeeld uit Excel: UC = 61,56 / 90,00 = 0,684."""
    p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=2.6,
        inheiniveau=-1.0,
        grondgewicht=19.0,
        grondwaterstand=8.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert abs(p_stab - 61.56) < 0.01
    assert abs(p_water - 90.0) < 0.01
    assert abs(uc - 0.684) < 0.001
    assert uc < 1.0


def test_berekening_voldoet():
    """Situatie met geringe wateropdruk — UC >= 1,0."""
    _p_stab, _p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=0.0,
        inheiniveau=-6.0,
        grondgewicht=20.0,
        grondwaterstand=1.0,
        materiaalfactor=1.0,
        watergewicht=10.0,
    )
    assert uc >= 1.0


def test_berekening_nulwaterdruk():
    """Als grondwaterstand gelijk is aan inheiniveau is p_water nul -> inf."""
    _p_stab, p_water, uc = bereken_hydraulische_grondbreuk(
        bouwputniveau=0.0,
        inheiniveau=-5.0,
        grondgewicht=19.0,
        grondwaterstand=-5.0,
        materiaalfactor=0.9,
        watergewicht=10.0,
    )
    assert p_water == 0.0
    import math
    assert math.isinf(uc)


def test_extraheer_auto_waarden_volledig():
    """Extraheer inheiniveau, grondwaterstand en grondgewicht uit project."""
    project = _maak_project(inheiniveau=-3.5, grondwaterstand=5.0, grondgewicht=18.5)
    auto = extraheer_auto_waarden(project)
    assert auto.inheiniveau == -3.5
    assert auto.grondwaterstand == 5.0
    assert auto.grondgewicht == 18.5


def test_extraheer_auto_waarden_hoogste_waterpeil():
    """Bij meerdere waterpeilen wordt het hoogste gekozen."""
    damwand = SheetPilingElement(name='AZ', x=0.0, bottom=-2.0, top=1.0, width=0.9)
    grond = Soil(name='Zand', color='rgb(0,0,0)', color_int=None, gamma_wet=19.0)
    project = Project(
        base_name='test', project_name='Test',
        file_bundle=FileBundle(),
        sheet_piling=[damwand],
        waterlevels=[
            WaterLevel(name='Laag', level=2.0),
            WaterLevel(name='Hoog', level=6.0),
            WaterLevel(name='Midden', level=4.0),
        ],
        soils=[grond],
    )
    auto = extraheer_auto_waarden(project)
    assert auto.grondwaterstand == 6.0


def test_extraheer_auto_waarden_leeg_project():
    """Lege lijsten geven None terug - geen crash."""
    project = Project(
        base_name='test', project_name='Test',
        file_bundle=FileBundle(),
    )
    auto = extraheer_auto_waarden(project)
    assert auto.inheiniveau is None
    assert auto.grondwaterstand is None
    assert auto.grondgewicht is None
