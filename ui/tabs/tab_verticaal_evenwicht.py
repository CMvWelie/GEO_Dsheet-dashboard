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


# ------------------------------------------------------------------
# Surface-extractie
# ------------------------------------------------------------------

def _zoek_bodem_punten(surface: Surface) -> tuple[float, float, float]:
    """Geeft (x_links, x_rechts, min_y) van de twee laagste Surface-punten.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel.

    Returns
    -------
    tuple[float, float, float]
        (x_links, x_rechts, ontgravingsniveau_m_NAP).
    """
    min_y = min(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_links = min(pt['x'] for pt in bodem)
    x_rechts = max(pt['x'] for pt in bodem)
    return x_links, x_rechts, min_y


def extraheer_talud_links(surface: Surface) -> TaludGeometrie:
    """Leid maaiveldniveau en helling af voor het linkse talud.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel (dekt volledige breedte).

    Returns
    -------
    TaludGeometrie
        Maaiveldniveau en helling_h_per_v (0.0 bij vlak terrein).
    """
    min_y = min(pt['y'] for pt in surface.points)
    maaiveld_niveau = max(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_links_bodem = min(pt['x'] for pt in bodem)
    links_punten = [pt for pt in surface.points if pt['x'] <= x_links_bodem]
    d1 = maaiveld_niveau - min_y
    if not links_punten or d1 <= 0.0:
        return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=0.0)
    x_top_links = min(pt['x'] for pt in links_punten)
    dx = x_links_bodem - x_top_links
    return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=dx / d1)


def extraheer_talud_rechts(surface: Surface) -> TaludGeometrie:
    """Leid maaiveldniveau en helling af voor het rechtse talud.

    Parameters
    ----------
    surface: D-Sheet maaiveldprofiel (dekt volledige breedte).

    Returns
    -------
    TaludGeometrie
        Maaiveldniveau en helling_h_per_v (0.0 bij vlak terrein).
    """
    min_y = min(pt['y'] for pt in surface.points)
    maaiveld_niveau = max(pt['y'] for pt in surface.points)
    bodem = [pt for pt in surface.points if abs(pt['y'] - min_y) <= 0.01]
    x_rechts_bodem = max(pt['x'] for pt in bodem)
    rechts_punten = [pt for pt in surface.points if pt['x'] >= x_rechts_bodem]
    d1 = maaiveld_niveau - min_y
    if not rechts_punten or d1 <= 0.0:
        return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=0.0)
    x_top_rechts = max(pt['x'] for pt in rechts_punten)
    dx = x_top_rechts - x_rechts_bodem
    return TaludGeometrie(maaiveld_niveau=maaiveld_niveau, helling_h_per_v=dx / d1)


def extraheer_auto_waarden_ve(
    project: Project,
    stage_naam: str,
    profiel_zijde: str,
) -> AutoWaardenVE:
    """Extraheert auto-invulwaarden voor verticaal evenwicht uit een Project.

    Parameters
    ----------
    project:      Geparseerd D-Sheet project.
    stage_naam:   Naam van de te gebruiken rekenfase.
    profiel_zijde: 'links' of 'rechts' — welk grondprofiel als basis.

    Returns
    -------
    AutoWaardenVE
        Alle auto-waarden; velden zijn None als bron ontbreekt.
    """
    def _find_surface(naam: str) -> Surface | None:
        return next((s for s in project.surfaces if s.name == naam), None)

    stage = next((s for s in project.stages if s.name == stage_naam), None)

    stijghoogte = max((wl.level for wl in project.waterlevels), default=None)

    surf_links_naam = stage.left_surface if stage else None
    surf_rechts_naam = stage.right_surface if stage else None
    surf_links = _find_surface(surf_links_naam) if surf_links_naam else None
    surf_rechts = _find_surface(surf_rechts_naam) if surf_rechts_naam else None

    ref_surf = surf_links or surf_rechts
    breedte = None
    ontgravingsniveau = None
    if ref_surf and ref_surf.points:
        x_l, x_r, min_y = _zoek_bodem_punten(ref_surf)
        breedte = abs(x_r - x_l)
        ontgravingsniveau = min_y

    talud_links = extraheer_talud_links(surf_links) if surf_links and surf_links.points else None
    talud_rechts = extraheer_talud_rechts(surf_rechts) if surf_rechts and surf_rechts.points else None

    profiel_naam = (
        (stage.left_profile if profiel_zijde == 'links' else stage.right_profile)
        if stage else None
    )
    profiel = next((p for p in project.profiles if p.name == profiel_naam), None)
    soil_map = {s.name: s for s in project.soils}
    grondlagen: list[tuple[str, float, float, float, float]] = []
    if profiel and profiel.layers:
        for i, laag in enumerate(profiel.layers):
            ok = (
                profiel.layers[i + 1].level
                if i + 1 < len(profiel.layers)
                else laag.level - 30.0
            )
            bodem = soil_map.get(laag.material)
            gamma_dr = bodem.gamma_dry if bodem else 0.0
            gamma_nat = bodem.gamma_wet if bodem else 0.0
            grondlagen.append((laag.material, laag.level, ok, gamma_dr, gamma_nat))

    return AutoWaardenVE(
        ontgravingsniveau=ontgravingsniveau,
        breedte_bouwputbodem=breedte,
        stijghoogte=stijghoogte,
        waterpeil_bouwput=stijghoogte,
        grondlagen=grondlagen,
        talud_links=talud_links,
        talud_rechts=talud_rechts,
    )
