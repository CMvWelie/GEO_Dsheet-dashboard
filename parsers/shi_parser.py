"""Parser voor D-Sheet invoerbestanden (.shi, .shd, .shs).

Alle functies zijn 1-op-1 geporteerd vanuit Dsheet_dashboard_v89.html.
"""

from __future__ import annotations
import re
import math

from parsers.base_parser import extract_section, find_line_value
from parsers.models import (
    Soil, SoilProfile, SoilLayer, Surface, WaterLevel, SheetPilingElement,
    Anchor, Strut, SpringSupport, RigidSupport, HorizontalLineLoad,
    Moment, NormalForce, UniformLoad, SurchargeLoad, Stage,
    FileBundle, Project,
    ResultStep, ResultStage, ResultPoint,
    AnchorStrutResumeItem, SupportResumeItem,
    ResultSummary,
)
from utils.color_utils import parse_color_int


# ---------------------------------------------------------------------------
# Naam-normalisatie
# ---------------------------------------------------------------------------

def _normalize_name(value: str) -> str:
    """Normaliseer een profielnaam voor vergelijking (lowercase, enkelvoudige spaties)."""
    return re.sub(r'\s+', ' ', str(value or '')).strip().lower()


# ---------------------------------------------------------------------------
# Projectnaam
# ---------------------------------------------------------------------------

def parse_project_name(source_text: str, fallback_name: str) -> str:
    """Lees de projectnaam uit de FILENAME-regel of gebruik fallback_name.

    Parameters
    ----------
    source_text:   Tekst van het primaire bronbestand (.shi of .shd).
    fallback_name: Bestandsnaam zonder extensie als terugvalwaarde.

    Returns
    -------
    str  Projectnaam zonder extensie.
    """
    from_filename = find_line_value(source_text, r'^FILENAME\s*:\s*(.+)$')
    if from_filename:
        parts = re.split(r'[\\/]', from_filename)
        return re.sub(r'\.(shi|shd|shs)$', '', parts[-1], flags=re.IGNORECASE)
    return fallback_name


# ---------------------------------------------------------------------------
# Grondsoorten
# ---------------------------------------------------------------------------

def parse_soils(text: str) -> list[Soil]:
    """Parseer alle [SOIL]...[END OF SOIL] blokken.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Soil]  Lijst van grondsoort-objecten met naam en kleur.
    """
    out: list[Soil] = []
    for m in re.finditer(r'\[SOIL\]([\s\S]*?)\[END OF SOIL\]', text, re.IGNORECASE):
        block = m.group(1).strip()
        lines = [ln.strip() for ln in block.split('\n') if ln.strip()]
        name = lines[0] if lines else f'Soil {len(out) + 1}'
        color_match = re.search(r'SoilColor\s*=\s*(\d+)', block, re.IGNORECASE)
        color_int = int(color_match.group(1)) if color_match else None
        color = parse_color_int(color_int) if color_int is not None else 'rgb(220, 220, 220)'
        out.append(Soil(
            name=name,
            color=color,
            color_int=color_int,
            gamma_dry=float(find_line_value(block, r'^SoilGamDry\s*=\s*(.+)$') or 0),
            gamma_wet=float(find_line_value(block, r'^SoilGamWet\s*=\s*(.+)$') or 0),
            cohesion=float(find_line_value(block, r'^SoilCohesion\s*=\s*(.+)$') or 0),
            phi=float(find_line_value(block, r'^SoilPhi\s*=\s*(.+)$') or 0),
            delta=float(find_line_value(block, r'^SoilDelta\s*=\s*(.+)$') or 0),
            kh1=float(find_line_value(block, r'^SoilCurKo1\s*=\s*(.+)$') or 0),
            kh2=float(find_line_value(block, r'^SoilCurKo2\s*=\s*(.+)$') or 0),
            kh3=float(find_line_value(block, r'^SoilCurKo3\s*=\s*(.+)$') or 0),
        ))
    return out


# ---------------------------------------------------------------------------
# Grondprofielen
# ---------------------------------------------------------------------------

def parse_soil_profiles(text: str) -> list[SoilProfile]:
    """Parseer de SOIL PROFILES sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[SoilProfile]  Profielen met lagen en optionele x,y-coördinaten.
    """
    sec = extract_section(text, 'SOIL PROFILES')
    if not sec:
        return []
    lines = sec.split('\n')
    profiles: list[SoilProfile] = []
    i = 0
    occurrence = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Sla koptekstregels over
        if (re.match(r'^\d+\s+Number of spring characteristics curves', line, re.IGNORECASE)
                or re.match(r'^\d+\s+1\/0', line, re.IGNORECASE)
                or re.match(r'^\d+\s+Number of soil profiles', line, re.IGNORECASE)
                or re.match(r'^Nr\s+Level', line, re.IGNORECASE)
                or re.search(r'Number of soil layers per soil profile', line, re.IGNORECASE)):
            i += 1
            continue
        # Sla data-rijen over (4+ getallen op één regel)
        if re.match(r'^\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+', line):
            i += 1
            continue

        # Dit is een profielnaam
        profile = SoilProfile(
            name=line,
            normalized_name=_normalize_name(line),
            occurrence=occurrence,
            x=None,
            y=None,
            layers=[]
        )
        occurrence += 1
        i += 1
        seen_layer_header = False

        while i < len(lines):
            cur = lines[i].strip()
            if not cur:
                i += 1
                continue
            mx = re.match(r'^([-\d.]+)\s+X coordinate$', cur, re.IGNORECASE)
            if mx:
                profile.x = float(mx.group(1))
                i += 1
                continue
            my = re.match(r'^([-\d.]+)\s+Y coordinate$', cur, re.IGNORECASE)
            if my:
                profile.y = float(my.group(1))
                i += 1
                continue
            if (re.match(r'^Nr\s+Level', cur, re.IGNORECASE)
                    or re.search(r'Number of soil layers per soil profile', cur, re.IGNORECASE)):
                seen_layer_header = True
                i += 1
                continue
            layer_m = re.match(r'^(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+(.+)$', cur)
            if layer_m:
                profile.layers.append(SoilLayer(
                    nr=int(layer_m.group(1)),
                    level=float(layer_m.group(2)),
                    wosp_top=float(layer_m.group(3)),
                    wosp_bottom=float(layer_m.group(4)),
                    material=layer_m.group(5).strip()
                ))
                i += 1
                continue
            if not seen_layer_header and re.match(r'^\d+\s+', cur):
                i += 1
                continue
            break

        if profile.layers:
            profiles.append(profile)

    return profiles


# ---------------------------------------------------------------------------
# Maaiveldprofielen (surfaces)
# ---------------------------------------------------------------------------

def parse_surfaces(text: str) -> list[Surface]:
    """Parseer de SURFACES sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Surface]  Maaiveldprofielen met puntenreeksen.
    """
    sec = extract_section(text, 'SURFACES')
    if not sec:
        return []
    lines = sec.split('\n')
    surfaces: list[Surface] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        header = re.match(r'^(\d+)\s+(\d+)\s+(.+)$', line)
        if header:
            surface = Surface(nr=int(header.group(1)), name=header.group(3).strip(), points=[])
            i += 1
            while i < len(lines):
                cur = lines[i].strip()
                if not cur:
                    i += 1
                    continue
                pt = re.match(r'^(\d+)\s+([-\d.]+)\s+([-\d.]+)$', cur)
                if pt:
                    surface.points.append({
                        'nr': int(pt.group(1)),
                        'x': float(pt.group(2)),
                        'y': float(pt.group(3))
                    })
                    i += 1
                    continue
                if (re.match(r'^(\d+)\s+(\d+)\s+(.+)$', cur)
                        and not re.search(r'Standard deviation|Distribution type', cur)):
                    break
                i += 1
            surfaces.append(surface)
            continue
        i += 1
    return surfaces


# ---------------------------------------------------------------------------
# Waterpeilen
# ---------------------------------------------------------------------------

def parse_water_levels(text: str) -> list[WaterLevel]:
    """Parseer de WATERLEVELS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[WaterLevel]  Lijst van waterpeilen met naam en niveau.
    """
    sec = extract_section(text, 'WATERLEVELS')
    if not sec:
        return []
    lines = [ln.strip() for ln in sec.split('\n') if ln.strip()]
    out: list[WaterLevel] = []
    i = 0
    while i < len(lines) - 1:
        if not re.match(r'^[-\d.]+$', lines[i]) and re.match(r'^[-\d.]+$', lines[i + 1]):
            out.append(WaterLevel(name=lines[i], level=float(lines[i + 1])))
            i += 2
        else:
            i += 1
    return out


# ---------------------------------------------------------------------------
# Damwandprofiel
# ---------------------------------------------------------------------------

def parse_sheet_piling(text: str) -> list[SheetPilingElement]:
    """Parseer de SHEET PILING sectie inclusief individuele elementen.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[SheetPilingElement]  Damwandsegmenten gesorteerd van boven naar beneden.
    """
    sec = extract_section(text, 'SHEET PILING')
    if not sec:
        return []
    top_match = re.search(r'([-\d.]+)\s+Level top sheet piling', sec, re.IGNORECASE)
    common_top = float(top_match.group(1)) if top_match else None
    out: list[SheetPilingElement] = []
    for m in re.finditer(r'\[SHEET PILING ELEMENT\]([\s\S]*?)\[END OF SHEET PILING ELEMENT\]',
                          sec, re.IGNORECASE):
        block = m.group(1)
        lines_b = [ln.strip() for ln in block.split('\n') if ln.strip()]
        name = lines_b[0] if lines_b else f'Damwand {len(out) + 1}'
        # Staalkwaliteit: haal tekst tussen haakjes op, bv. "AZ 13-700 (S240GP)" → "S240GP"
        kwaliteit_m = re.search(r'\(([^)]+)\)', name)
        staal = kwaliteit_m.group(1) if kwaliteit_m else ''

        max_char = float(find_line_value(block, r'^SheetPilingElementMaxCharacteristicMoment\s*=\s*(.+)$') or 0)
        kmod = float(find_line_value(block, r'^SheetPilingElementKMod\s*=\s*(.+)$') or 1)
        mat_f = float(find_line_value(block, r'^SheetPilingElementMaterialFactor\s*=\s*(.+)$') or 1)
        red_f = float(find_line_value(block, r'^sSheetPilingElementReductionFactorMaxMoment\s*=\s*(.+)$') or 1)
        pile_w_raw = float(find_line_value(block, r'^SheetPilingPileWidth\s*=\s*(.+)$') or 0)

        out.append(SheetPilingElement(
            name=name,
            x=float(find_line_value(block, r'^SheetPilingElementX=(.+)$') or 0),
            bottom=float(find_line_value(block, r'^SheetPilingElementLevel=(.+)$') or 0),
            top=common_top,
            width=float(find_line_value(block, r'^SheetPilingElementWidth=(.+)$') or 1),
            height_mm=float(find_line_value(block, r'^SheetPilingElementHeight\s*=\s*(.+)$') or 0),
            pile_width_mm=pile_w_raw * 1000,
            ei_knm2_per_m=float(find_line_value(block, r'^SheetPilingElementEI\s*=\s*(.+)$') or 0),
            section_area_cm2=float(find_line_value(block, r'^SheetPilingElementSectionArea\s*=\s*(.+)$') or 0),
            resisting_moment_cm3=float(find_line_value(block, r'^SheetPilingElementResistingMoment\s*=\s*(.+)$') or 0),
            max_char_moment_knm=max_char,
            opneembaar_moment_knm=max_char * kmod * mat_f * red_f,
            steel_quality=staal,
        ))
    out.sort(key=lambda el: el.bottom if math.isfinite(el.bottom) else -math.inf, reverse=True)
    for idx, el in enumerate(out):
        el.segment_top = common_top if idx == 0 else out[idx - 1].bottom
        el.segment_bottom = el.bottom
    return out


# ---------------------------------------------------------------------------
# Ankers, stempels, veren, stijve steunen
# ---------------------------------------------------------------------------

def parse_anchors(text: str) -> list[Anchor]:
    """Parseer de ANCHORS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Anchor]  Lijst van anker-objecten.
    """
    sec = extract_section(text, 'ANCHORS')
    if not sec:
        return []
    out: list[Anchor] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 10 and re.match(r'^\d+$', parts[0]) and re.match(r'^[-\d.]+$', parts[1]):
            out.append(Anchor(
                nr=int(parts[0]),
                level=float(parts[1]),
                emod=float(parts[2]),
                cross_section=float(parts[3]),
                length=float(parts[4]),
                yield_f=float(parts[5]),
                angle=float(parts[6]),
                height=float(parts[7]),
                side=int(parts[8]),
                name=' '.join(parts[9:])
            ))
    return out


def parse_struts(text: str) -> list[Strut]:
    """Parseer de STRUTS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Strut]  Lijst van stempel-objecten.
    """
    sec = extract_section(text, 'STRUTS')
    if not sec:
        return []
    out: list[Strut] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 10 and re.match(r'^\d+$', parts[0]) and re.match(r'^[-\d.]+$', parts[1]):
            out.append(Strut(
                nr=int(parts[0]),
                level=float(parts[1]),
                emod=float(parts[2]),
                cross_section=float(parts[3]),
                length=float(parts[4]),
                yield_f=float(parts[5]),
                angle=float(parts[6]),
                aux=float(parts[7]),
                side=int(parts[8]),
                name=' '.join(parts[9:])
            ))
    return out


def parse_spring_supports(text: str) -> list[SpringSupport]:
    """Parseer de SPRING SUPPORTS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[SpringSupport]  Lijst van veersteun-objecten.
    """
    sec = extract_section(text, 'SPRING SUPPORTS')
    if not sec:
        return []
    out: list[SpringSupport] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 5 and re.match(r'^\d+$', parts[0]) and re.match(r'^[-\d.]+$', parts[1]):
            out.append(SpringSupport(
                nr=int(parts[0]),
                level=float(parts[1]),
                rot_stiff=float(parts[2]),
                tr_stiff=float(parts[3]),
                name=' '.join(parts[4:])
            ))
    return out


def parse_rigid_supports(text: str) -> list[RigidSupport]:
    """Parseer de RIGID SUPPORTS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[RigidSupport]  Lijst van stijve steun-objecten.
    """
    sec = extract_section(text, 'RIGID SUPPORTS')
    if not sec:
        return []
    out: list[RigidSupport] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 5 and re.match(r'^\d+$', parts[0]) and re.match(r'^[-\d.]+$', parts[1]):
            out.append(RigidSupport(
                nr=int(parts[0]),
                level=float(parts[1]),
                rot_stiff=float(parts[2]),
                tr_stiff=float(parts[3]),
                name=' '.join(parts[4:])
            ))
    return out


# ---------------------------------------------------------------------------
# Belastingen
# ---------------------------------------------------------------------------

def parse_horizontal_line_loads(text: str) -> list[HorizontalLineLoad]:
    """Parseer de HORIZONTAL LINE LOADS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[HorizontalLineLoad]  Lijst van horizontale lijnlasten.
    """
    sec = extract_section(text, 'HORIZONTAL LINE LOADS')
    if not sec:
        return []
    out: list[HorizontalLineLoad] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 6 and re.match(r'^\d+$', parts[0]):
            out.append(HorizontalLineLoad(
                nr=int(parts[0]),
                level=float(parts[1]),
                value=float(parts[2]),
                permanent=float(parts[3]),
                favourable=float(parts[4]),
                name=' '.join(parts[5:])
            ))
    return out


def parse_moments(text: str) -> list[Moment]:
    """Parseer de MOMENTS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Moment]  Lijst van moment-objecten.
    """
    sec = extract_section(text, 'MOMENTS')
    if not sec:
        return []
    out: list[Moment] = []
    for line in sec.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 6 and re.match(r'^\d+$', parts[0]):
            out.append(Moment(
                nr=int(parts[0]),
                level=float(parts[1]),
                value=float(parts[2]),
                permanent=float(parts[3]),
                favourable=float(parts[4]),
                name=' '.join(parts[5:])
            ))
    return out


def parse_normal_forces(text: str) -> list[NormalForce]:
    """Parseer de NORMAL FORCES sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[NormalForce]  Lijst van normaalkracht-objecten.
    """
    sec = extract_section(text, 'NORMAL FORCES')
    if not sec:
        return []
    out: list[NormalForce] = []
    for line in sec.split('\n'):
        m = re.match(
            r'^(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+(.+)$',
            line.strip()
        )
        if m:
            out.append(NormalForce(
                nr=int(m.group(1)),
                top=float(m.group(2)),
                surface_left=float(m.group(3)),
                surface_right=float(m.group(4)),
                bottom=float(m.group(5)),
                permanent=int(m.group(6)),
                favourable=int(m.group(7)),
                name=m.group(8).strip()
            ))
    return out


def _parse_load_blocks(section_text: str, mode: str) -> list[UniformLoad | SurchargeLoad]:
    """Generieke parser voor [LOAD]...[END OF LOAD] blokken.

    Parameters
    ----------
    section_text: Tekst van de betreffende sectie.
    mode:         'uniform' of 'surcharge'.

    Returns
    -------
    list  UniformLoad- of SurchargeLoad-objecten.
    """
    if not section_text:
        return []
    out = []
    for m in re.finditer(r'\[LOAD\]([\s\S]*?)\[END OF LOAD\]', section_text, re.IGNORECASE):
        block = m.group(1).strip()
        lines_b = [ln.strip() for ln in block.split('\n') if ln.strip()]
        name = lines_b[0] if lines_b else f'{mode} {len(out) + 1}'
        if mode == 'uniform':
            out.append(UniformLoad(
                name=name,
                left=float(find_line_value(block, r'^UniformLoadLeft=(.+)$') or 0),
                right=float(find_line_value(block, r'^UniformLoadRight=(.+)$') or 0),
                permanent=float(find_line_value(block, r'^UniformLoadPermanent=(.+)$') or 0),
                favourable=float(find_line_value(block, r'^UniformLoadFavourable=(.+)$') or 0),
            ))
        elif mode == 'surcharge':
            points = [
                {'distance': float(mx.group(1)), 'value': float(mx.group(2))}
                for mx in re.finditer(
                    r'SurchargeLoadDistance\s*=\s*([-\d.]+)\s*[\r\n]+SurchargeLoadValue\s*=\s*([-\d.]+)',
                    block, re.IGNORECASE
                )
            ]
            out.append(SurchargeLoad(name=name, points=points))
    return out


def parse_uniform_loads(text: str) -> list[UniformLoad]:
    """Parseer de UNIFORM LOADS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[UniformLoad]
    """
    return _parse_load_blocks(extract_section(text, 'UNIFORM LOADS'), 'uniform')  # type: ignore[return-value]


def parse_surcharge_loads(text: str) -> list[SurchargeLoad]:
    """Parseer de SURCHARGE LOADS sectie.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[SurchargeLoad]
    """
    return _parse_load_blocks(extract_section(text, 'SURCHARGE LOADS'), 'surcharge')  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Bouwfases (state machine)
# ---------------------------------------------------------------------------

def parse_stages(text: str) -> list[Stage]:
    """Parseer de CONSTRUCTION STAGES sectie.

    Complexe state machine die per fase de actieve belastingen,
    steunen en profielen registreert.

    Parameters
    ----------
    text: Gecombineerde bestandstekst.

    Returns
    -------
    list[Stage]  Bouwfases in volgorde.
    """
    sec = extract_section(text, 'CONSTRUCTION STAGES')
    if not sec:
        return []
    lines = sec.split('\n')
    stages: list[Stage] = []
    i = 0

    while i < len(lines):
        name = lines[i].strip()
        if (not name
                or re.match(r'^\d+\s+Number of Construction stages', name, re.IGNORECASE)
                or re.search(r'Method Left:', name, re.IGNORECASE)):
            i += 1
            continue

        stage = Stage(name=name)
        stage.method_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
        stage.left_surface = lines[i + 2].strip() if i + 2 < len(lines) else ''
        stage.right_surface = lines[i + 3].strip() if i + 3 < len(lines) else ''
        stage.left_water = lines[i + 4].strip() if i + 4 < len(lines) else ''
        stage.right_water = lines[i + 5].strip() if i + 5 < len(lines) else ''
        stage.left_profile = lines[i + 6].strip() if i + 6 < len(lines) else ''
        stage.right_profile = lines[i + 7].strip() if i + 7 < len(lines) else ''
        i += 8

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                break
            # Detecteer begin van volgende fase
            if (not re.match(r'^[-\d]', line)
                    and i + 1 < len(lines)
                    and re.search(r'Method Left:', lines[i + 1], re.IGNORECASE)):
                break

            m = re.match(r'^(\d+)\s+Anchors present in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+[-\d.]+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.anchors.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Struts present in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+[-\d.]+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.struts.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Spring supports present in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.spring_supports.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Rigid supports present in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.rigid_supports.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Uniform loads in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.uniform_loads.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+(\d+)\s+Surcharge loads in stage', line, re.IGNORECASE)
            if m:
                count_left = int(m.group(1))
                count_right = int(m.group(2))
                count = count_left + count_right
                i += 1
                for k in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        load_name = mm.group(1).strip()
                        stage.surcharge_loads.append(load_name)
                        if k < count_left:
                            stage.surcharge_loads_left.append(load_name)
                        else:
                            stage.surcharge_loads_right.append(load_name)
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Horizontal line loads in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.horizontal_line_loads.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Moments in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.moments.append(mm.group(1).strip())
                    i += 1
                continue

            m = re.match(r'^(\d+)\s+Normal forces in stage', line, re.IGNORECASE)
            if m:
                count = int(m.group(1))
                i += 1
                for _ in range(count):
                    if i >= len(lines):
                        break
                    mm = re.match(r'^\d+\s+(.+)$', lines[i].strip())
                    if mm:
                        stage.normal_forces.append(mm.group(1).strip())
                    i += 1
                continue

            i += 1

        stages.append(stage)

    return stages


# ---------------------------------------------------------------------------
# .shd resultaatparsers
# ---------------------------------------------------------------------------

def _normalize_verify_step_key(raw_step: str) -> str:
    """Normaliseer een VERIFY STEP-label naar een consistente sleutelstring."""
    s = str(raw_step or '').strip()
    for suffix in [
        ' (SERVICEABILITY LIMIT STATE)',
        ' (LOW MODULUS OF SUBGRADE REACTION AND LOW PASSIVE WATER LEVEL)',
        ' (HIGH MODULUS OF SUBGRADE REACTION AND LOW PASSIVE WATER LEVEL)',
        ' (LOW MODULUS OF SUBGRADE REACTION AND HIGH PASSIVE WATER LEVEL)',
        ' (HIGH MODULUS OF SUBGRADE REACTION AND HIGH PASSIVE WATER LEVEL)',
    ]:
        s = s.replace(suffix, '')
    s = s.replace(' MULTIPLIED BY FACTOR', ' x factor')
    return s


def parse_result_steps_from_shd(text: str) -> dict[str, ResultStep]:
    """Parseer alle VERIFY STEP blokken uit een .shd resultaatbestand.

    Parameters
    ----------
    text: Volledige inhoud van het .shd bestand.

    Returns
    -------
    dict[str, ResultStep]  Sleutel = genormaliseerd stap-label.
    """
    result: dict[str, ResultStep] = {}
    lines = text.split('\n')
    i = 0
    current_key: str | None = None
    pending_depths: list[float] | None = None

    while i < len(lines):
        s = lines[i].strip()

        vm = re.match(r'^\[VERIFY STEP (.+)\]$', s)
        if vm:
            current_key = _normalize_verify_step_key(vm.group(1).strip())
            if current_key not in result:
                result[current_key] = ResultStep(raw_step=vm.group(1).strip())
            pending_depths = None
            i += 1
            continue

        if s.startswith('[END OF VERIFY STEP'):
            current_key = None
            pending_depths = None
            i += 1
            continue

        if s == '[POINTS ON SHEETPILE]' and current_key:
            j = i + 1
            while j < len(lines) and lines[j].strip() != '[DATA]':
                j += 1
            j += 1
            depths: list[float] = []
            while j < len(lines) and lines[j].strip() != '[END OF DATA]':
                val = lines[j].strip()
                if val:
                    try:
                        depths.append(float(val))
                    except ValueError:
                        pass
                j += 1
            if depths:
                pending_depths = depths
                result[current_key].depths = depths[:]
            i = j + 1
            continue

        if s == '[CONSTRUCTION STAGE]' and current_key:
            stage_number: int | None = None
            j = i + 1
            while j < len(lines) and lines[j].strip() != '[MOMENTS FORCES DISPLACEMENTS]':
                sm = re.match(r'^StageNumber=(\d+)$', lines[j].strip())
                if sm:
                    stage_number = int(sm.group(1))
                if lines[j].strip() == '[END OF CONSTRUCTION STAGE]':
                    break
                j += 1

            if j < len(lines) and lines[j].strip() == '[MOMENTS FORCES DISPLACEMENTS]':
                k = j + 1
                while k < len(lines) and lines[k].strip() != '[DATA]':
                    k += 1
                k += 1
                series: list[tuple[float, float, float]] = []
                while k < len(lines) and lines[k].strip() != '[END OF DATA]':
                    row = lines[k].strip()
                    if row:
                        parts = row.split()
                        if len(parts) >= 3:
                            try:
                                moment, shear, disp = float(parts[0]), float(parts[1]), float(parts[2])
                                series.append((moment, shear, disp))
                            except ValueError:
                                pass
                    k += 1

                if stage_number and pending_depths and series:
                    n = min(len(pending_depths), len(series))
                    pts = [
                        ResultPoint(
                            depth=pending_depths[idx],
                            moment=series[idx][0],
                            shear=series[idx][1],
                            disp=series[idx][2]
                        )
                        for idx in range(n)
                    ]
                    result[current_key].stages[stage_number] = ResultStage(
                        stage_number=stage_number,
                        points=pts
                    )
                i = k + 1
                continue

        i += 1

    # Verwijder stappen zonder data
    return {k: v for k, v in result.items() if v.stages}


def parse_anchors_and_struts_resume(shd_text: str) -> list[AnchorStrutResumeItem]:
    """Parseer de ANCHORS AND STRUTS RESUME tabel uit het .shd bestand.

    Parameters
    ----------
    shd_text: Volledige inhoud van het .shd bestand.

    Returns
    -------
    list[AnchorStrutResumeItem]
    """
    out: list[AnchorStrutResumeItem] = []
    m = re.search(
        r'\[ANCHORS AND STRUTS RESUME\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
        shd_text
    )
    if not m:
        return out
    for raw_line in m.group(1).split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        qm = re.match(r"^(.*?)'([^']+)'$", line)
        if not qm:
            continue
        nums_str = qm.group(1).strip().split()
        try:
            nums = [float(x) for x in nums_str]
        except ValueError:
            continue
        if len(nums) < 10 or not all(math.isfinite(n) for n in nums):
            continue
        out.append(AnchorStrutResumeItem(
            stage_number=int(nums[0]),
            verification_type=int(nums[1]),
            basis_cur_step=int(nums[2]),
            partial_factor_set=int(nums[3]),
            representative_factor=nums[4],
            force=nums[5],
            anchor_type=int(nums[6]),
            anchor_state=int(nums[7]),
            changed_to_yielding=int(nums[8]),
            calculation_status=int(nums[9]),
            name=qm.group(2)
        ))
    return out


def parse_supports_resume(shd_text: str) -> list[SupportResumeItem]:
    """Parseer de SUPPORTS RESUME tabel uit het .shd bestand.

    Parameters
    ----------
    shd_text: Volledige inhoud van het .shd bestand.

    Returns
    -------
    list[SupportResumeItem]
    """
    out: list[SupportResumeItem] = []
    m = re.search(
        r'\[SUPPORTS RESUME\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
        shd_text
    )
    if not m:
        return out
    for raw_line in m.group(1).split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        qm = re.match(r"^(.*?)'([^']+)'$", line)
        if not qm:
            continue
        nums_str = qm.group(1).strip().split()
        try:
            nums = [float(x) for x in nums_str]
        except ValueError:
            continue
        if len(nums) < 9 or not all(math.isfinite(n) for n in nums):
            continue
        out.append(SupportResumeItem(
            stage_number=int(nums[0]),
            verification_type=int(nums[1]),
            basis_cur_step=int(nums[2]),
            partial_factor_set=int(nums[3]),
            representative_factor=nums[4],
            force=nums[5],
            moment=nums[6],
            support_rigidity_type=int(nums[7]),
            calculation_status=int(nums[8]),
            name=qm.group(2)
        ))
    return out


# ---------------------------------------------------------------------------
# Resultaatsamenvatting per constructiefase
# ---------------------------------------------------------------------------

def _float_pattern(tekst: str, patroon: str) -> float | None:
    """Zoek een float-waarde via regex-patroon in tekst."""
    m = re.search(patroon, tekst)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def parse_result_summaries(shd_text: str) -> list[ResultSummary]:
    """Parseer CONSTRUCTION STAGE blokken uit .shd voor resultaatsamenvatting.

    Parseert alleen de constructiefasen uit de eerste VERIFY STEP sectie.
    Als er geen VERIFY STEP aanwezig is, wordt de volledige tekst doorzocht.
    Verplaatsingswaarden in het .shd-bestand zijn al in mm.

    Parameters
    ----------
    shd_text:
        Volledige inhoud van het .shd bestand.

    Returns
    -------
    list[ResultSummary]
        Eén samenvatting per constructiefase.
    """
    # Beperk tot de eerste VERIFY STEP sectie zodat we niet alle herhalingen parsen
    vs_m = re.search(
        r'\[VERIFY STEP[^\]]*\]([\s\S]*?)\[END OF VERIFY STEP',
        shd_text, re.IGNORECASE
    )
    zoektekst = vs_m.group(1) if vs_m else shd_text

    out: list[ResultSummary] = []
    for m in re.finditer(
        r'\[CONSTRUCTION STAGE\]([\s\S]*?)\[END OF CONSTRUCTION STAGE\]',
        zoektekst,
        re.IGNORECASE
    ):
        blok = m.group(1)

        # Stage-nummer
        sn_m = re.search(r'^StageNumber\s*=\s*(\d+)', blok, re.MULTILINE)
        if not sn_m:
            continue
        stage_nr = int(sn_m.group(1))

        # Mobilisatiepercentages uit SOIL COLLAPSE DATA
        mob_grond_l = _float_pattern(blok, r'([\d.]+)\s*:\s*Percentage mobilized resistance left')
        mob_grond_r = _float_pattern(blok, r'([\d.]+)\s*:\s*Percentage mobilized resistance right')
        mob_mom_l   = _float_pattern(blok, r'([\d.]+)\s*:\s*Max mobilized moment percentage left')
        mob_mom_r   = _float_pattern(blok, r'([\d.]+)\s*:\s*Max mobilized moment percentage right')
        mob_grond = max(mob_grond_l or 0.0, mob_grond_r or 0.0)
        mob_mom   = max(mob_mom_l or 0.0,   mob_mom_r or 0.0)

        # Moment / kracht / verplaatsing uit MOMENTS FORCES DISPLACEMENTS
        mfd_m = re.search(
            r'\[MOMENTS FORCES DISPLACEMENTS\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
            blok, re.IGNORECASE
        )
        max_mom = 0.0
        max_shear = 0.0
        max_disp_mm = 0.0
        if mfd_m:
            for rij in mfd_m.group(1).split('\n'):
                delen = rij.strip().split()
                if len(delen) >= 3:
                    try:
                        mom, shear, disp = float(delen[0]), float(delen[1]), float(delen[2])
                        max_mom   = max(max_mom,   abs(mom))
                        max_shear = max(max_shear, abs(shear))
                        max_disp_mm = max(max_disp_mm, abs(disp))  # waarden zijn al in mm
                    except ValueError:
                        pass

        # Ankerkrachten uit ANCHOR DATA tabel
        ondersteuningen: list[tuple[str, float, float]] = []
        anker_m = re.search(
            r'\[ANCHOR DATA\][\s\S]*?\[DATA\]([\s\S]*?)\[END OF DATA\]',
            blok, re.IGNORECASE
        )
        if anker_m:
            for rij in anker_m.group(1).split('\n'):
                rij = rij.strip()
                if not rij:
                    continue
                naam_m = re.match(r"^(.*?)'([^']+)'", rij)
                if naam_m:
                    cijfers = naam_m.group(1).strip().split()
                    naam = naam_m.group(2)
                    if len(cijfers) >= 2:
                        try:
                            niveau = float(cijfers[0])
                            kracht = float(cijfers[1])
                            ondersteuningen.append((naam, kracht, niveau))
                        except ValueError:
                            pass

        out.append(ResultSummary(
            stage_number=stage_nr,
            max_moment_knm=max_mom,
            max_shear_kn=max_shear,
            max_disp_mm=max_disp_mm,
            mob_moment_pct=mob_mom,
            mob_grond_pct=mob_grond,
            ondersteuningen=ondersteuningen,
        ))
    return out


# ---------------------------------------------------------------------------
# Hoofd-parseerfunctie
# ---------------------------------------------------------------------------

def parse_project(file_bundle: FileBundle, base_name: str) -> Project:
    """Parseer een volledige projectset vanuit een FileBundle.

    Parameters
    ----------
    file_bundle: FileBundle met .shi, .shd en/of .shs tekst.
    base_name:   Bestandsnaam zonder extensie.

    Returns
    -------
    Project  Volledig ingelezen project-object.
    """
    shi = file_bundle.shi or ''
    shd = file_bundle.shd or ''
    shs = file_bundle.shs or ''
    source = shi or shd or shs
    combined = '\n'.join(t for t in [shi, shd, shs] if t)

    soils = parse_soils(combined)
    profiles = parse_soil_profiles(combined)
    surfaces = parse_surfaces(combined)
    waterlevels = parse_water_levels(combined)
    sheet_piling = parse_sheet_piling(combined)
    anchors = parse_anchors(combined)
    struts = parse_struts(combined)
    spring_supports = parse_spring_supports(combined)
    rigid_supports = parse_rigid_supports(combined)
    uniform_loads = parse_uniform_loads(combined)
    surcharge_loads = parse_surcharge_loads(combined)
    horizontal_line_loads = parse_horizontal_line_loads(combined)
    moments = parse_moments(combined)
    normal_forces = parse_normal_forces(combined)
    stages = parse_stages(combined)

    result_summaries = parse_result_summaries(shd)

    return Project(
        base_name=base_name,
        project_name=parse_project_name(source, base_name),
        file_bundle=file_bundle,
        soils=soils,
        profiles=profiles,
        surfaces=surfaces,
        waterlevels=waterlevels,
        sheet_piling=sheet_piling,
        anchors=anchors,
        struts=struts,
        spring_supports=spring_supports,
        rigid_supports=rigid_supports,
        uniform_loads=uniform_loads,
        surcharge_loads=surcharge_loads,
        horizontal_line_loads=horizontal_line_loads,
        moments=moments,
        normal_forces=normal_forces,
        stages=stages,
        soil_color_map={s.name: s.color for s in soils},
        result_steps=parse_result_steps_from_shd(shd),
        anchor_strut_resume=parse_anchors_and_struts_resume(shd),
        supports_resume=parse_supports_resume(shd),
        result_summaries=result_summaries,
    )
