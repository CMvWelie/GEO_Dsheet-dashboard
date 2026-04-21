"""Subtab Verticaal evenwicht — opbarstcontrole conform NEN 9997-1:2025 §10.2."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from parsers.models import Project, Surface, SoilProfile, Stage


@dataclass
class TaludGeometrie:
    """Geometrie van één talud naast de bouwput."""
    maaiveld_niveau: float
    helling_h_per_v: float


@dataclass
class AutoWaardenVE:
    """Waarden die automatisch uit een Project worden ingevuld."""
    ontgravingsniveau: float | None
    breedte_bouwputbodem: float | None
    stijghoogte: float | None
    waterpeil_bouwput: float | None
    grondlagen: list[tuple[str, float, float, float, float]] = field(default_factory=list)
    # (naam, bovenkant_m_NAP, onderkant_m_NAP, gamma_dr_kNm3, gamma_nat_kNm3)
    talud_links: TaludGeometrie | None = None
    talud_rechts: TaludGeometrie | None = None


def bereken_taludinvloed(d1: float, a: float, b: float, d2: float) -> float:
    """Bereken de f-factor voor taludinvloed conform NEN 9997-1:2025 art. 10.2.

    Parameters
    ----------
    d1: Hoogte van grond naast sleuf (maaiveld - ontgravingsniveau) [m].
    a:  Horizontale afstand van sleufrand tot teen talud (= d1 * h/v) [m].
    b:  Halve breedte bouwputbodem [m].
    d2: Diepte van ontgravingsniveau tot evenwichtsniveau [m].

    Returns
    -------
    float
        Dimensieloze f-factor [-].
    """
    if a <= 0.0 or b <= 0.0 or d1 <= 0.0:
        return 0.0
    b_over_a = b / a
    return (2.0 / math.pi) * (
        (1.0 + b_over_a) * math.atan(d2 / (a + b))
        - b_over_a * math.atan(d2 / b)
    )


def bereken_verticaal_evenwicht(
    lagen: list[tuple[str, float, float, float, float]],
    ontgravingsniveau: float,
    waterpeil_bouwput: float,
    stijghoogte: float,
    evenwichtsniveau: float,
    materiaalfactor: float,
    watergewicht: float,
) -> tuple[float, float, float]:
    """Bereken de verticaal-evenwichtcontrole (opbarsten) conform NEN 9997-1:2025 §10.2.

    Parameters
    ----------
    lagen:              Lijst (naam, bk, ok, γ_dr, γ_nat) — volledig profiel.
    ontgravingsniveau:  Bouwputniveau [m NAP].
    waterpeil_bouwput:  Freatisch peil in bouwput [m NAP].
    stijghoogte:        Artesiaanse stijghoogte w.v.p. [m NAP].
    evenwichtsniveau:   Onderkant waterremmende laag [m NAP].
    materiaalfactor:    γG;stb [-].
    watergewicht:       γ_w [kN/m³].

    Returns
    -------
    tuple[float, float, float]
        (Gstb_d [kN/m²], Vdst_d [kN/m²], UC [-]).
        UC is math.inf als Vdst_d nul is.
    """
    gstb = 0.0
    for _naam, bk, ok, gamma_dr, gamma_nat in lagen:
        effectief_bk = min(bk, ontgravingsniveau)
        effectief_ok = max(ok, evenwichtsniveau)
        if effectief_bk <= effectief_ok:
            continue
        dikte_boven = max(0.0, effectief_bk - max(effectief_ok, waterpeil_bouwput))
        dikte_onder = max(0.0, min(effectief_bk, waterpeil_bouwput) - effectief_ok)
        gstb += (dikte_boven * gamma_dr + dikte_onder * gamma_nat) * materiaalfactor

    vdst = max(0.0, (stijghoogte - evenwichtsniveau) * watergewicht)
    uc = gstb / vdst if vdst > 0.0 else math.inf
    return gstb, vdst, uc


def bereken_gewicht_talud(
    lagen: list[tuple[str, float, float, float, float]],
    maaiveld_niveau: float,
    ontgravingsniveau: float,
) -> float:
    """Gewicht van grond naast de sleuf (van maaiveld tot ontgravingsniveau) [kN/m²].

    Parameters
    ----------
    lagen:              Volledig grondprofiel (naam, bk, ok, γ_dr, γ_nat).
    maaiveld_niveau:    Maaiveldniveau aan de taludzijde [m NAP].
    ontgravingsniveau:  Bouwputniveau [m NAP].

    Returns
    -------
    float
        Neerwaarste druk uit het talud [kN/m²].
    """
    gewicht = 0.0
    for _naam, bk, ok, gamma_dr, _gamma_nat in lagen:
        effectief_bk = min(bk, maaiveld_niveau)
        effectief_ok = max(ok, ontgravingsniveau)
        if effectief_bk <= effectief_ok:
            continue
        gewicht += (effectief_bk - effectief_ok) * gamma_dr
    return gewicht
