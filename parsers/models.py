"""Dataclasses voor D-Sheet projectdata."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SoilLayer:
    nr: int
    level: float
    wosp_top: float
    wosp_bottom: float
    material: str


@dataclass
class SoilProfile:
    name: str
    normalized_name: str
    occurrence: int
    x: Optional[float]
    y: Optional[float]
    layers: list[SoilLayer] = field(default_factory=list)


@dataclass
class Soil:
    name: str
    color: str          # "rgb(r, g, b)"
    color_int: Optional[int]
    # Grondparameters
    gamma_dry: float = 0.0      # SoilGamDry  [kN/m³]
    gamma_wet: float = 0.0      # SoilGamWet  [kN/m³]
    cohesion: float = 0.0       # SoilCohesion [kN/m²]
    phi: float = 0.0            # SoilPhi [°]
    delta: float = 0.0          # SoilDelta [°]
    ka: float = 0.0             # SoilLa [-]
    kn: float = 0.0             # SoilLn [-]
    kp: float = 0.0             # SoilLp [-]
    ocr: float = 0.0            # SoilOCR [-]
    shell_factor: float = 0.0   # SoilShellFactor [-]
    kh1: float = 0.0            # SoilCurKo1 [kN/m³]
    kh2: float = 0.0            # SoilCurKo2 [kN/m³]
    kh3: float = 0.0            # SoilCurKo3 [kN/m³]


@dataclass
class Surface:
    nr: int
    name: str
    points: list[dict] = field(default_factory=list)   # [{nr, x, y}]


@dataclass
class WaterLevel:
    name: str
    level: float


@dataclass
class SheetPilingElement:
    name: str
    x: float
    bottom: float
    top: Optional[float]
    width: float
    segment_top: Optional[float] = None
    segment_bottom: Optional[float] = None
    # Profieleigenschappen
    height_mm: float = 0.0              # SheetPilingElementHeight [mm]
    pile_width_mm: float = 0.0          # SheetPilingPileWidth × 1000 [mm]
    ei_knm2_per_m: float = 0.0          # SheetPilingElementEI [kNm²/m]
    section_area_cm2: float = 0.0       # SheetPilingElementSectionArea [cm²/m]
    resisting_moment_cm3: float = 0.0   # SheetPilingElementResistingMoment [cm³/m]
    max_char_moment_knm: float = 0.0    # SheetPilingElementMaxCharacteristicMoment [kNm/m]
    opneembaar_moment_knm: float = 0.0  # max_char × KMod × MaterialFactor × ReductionFactor [kNm/m]
    steel_quality: str = ''             # afgeleid uit elementnaam, bv. "(S240GP)" → "S240GP"


@dataclass
class Anchor:
    nr: int
    level: float
    emod: float
    cross_section: float
    length: float
    yield_f: float
    angle: float
    height: float
    side: int
    name: str


@dataclass
class Strut:
    nr: int
    level: float
    emod: float
    cross_section: float
    length: float
    yield_f: float
    angle: float
    aux: float
    side: int
    name: str


@dataclass
class SpringSupport:
    nr: int
    level: float
    rot_stiff: float
    tr_stiff: float
    name: str


@dataclass
class RigidSupport:
    nr: int
    level: float
    rot_stiff: float
    tr_stiff: float
    name: str


@dataclass
class HorizontalLineLoad:
    nr: int
    level: float
    value: float
    permanent: float
    favourable: float
    name: str


@dataclass
class Moment:
    nr: int
    level: float
    value: float
    permanent: float
    favourable: float
    name: str


@dataclass
class NormalForce:
    nr: int
    top: float
    surface_left: float
    surface_right: float
    bottom: float
    permanent: int
    favourable: int
    name: str


@dataclass
class UniformLoad:
    name: str
    left: float
    right: float
    permanent: float
    favourable: float


@dataclass
class SurchargeLoad:
    name: str
    points: list[dict] = field(default_factory=list)  # [{distance, value}]


@dataclass
class Stage:
    name: str
    method_line: str = ""
    left_surface: str = ""
    right_surface: str = ""
    left_water: str = ""
    right_water: str = ""
    left_profile: str = ""
    right_profile: str = ""
    anchors: list[str] = field(default_factory=list)
    struts: list[str] = field(default_factory=list)
    spring_supports: list[str] = field(default_factory=list)
    rigid_supports: list[str] = field(default_factory=list)
    uniform_loads: list[str] = field(default_factory=list)
    surcharge_loads: list[str] = field(default_factory=list)
    surcharge_loads_left: list[str] = field(default_factory=list)
    surcharge_loads_right: list[str] = field(default_factory=list)
    horizontal_line_loads: list[str] = field(default_factory=list)
    moments: list[str] = field(default_factory=list)
    normal_forces: list[str] = field(default_factory=list)


@dataclass
class ResultPoint:
    depth: float
    moment: float
    shear: float
    disp: float


@dataclass
class ResultStage:
    stage_number: int
    points: list[ResultPoint] = field(default_factory=list)


@dataclass
class ResultStep:
    raw_step: str
    depths: list[float] = field(default_factory=list)
    stages: dict[int, ResultStage] = field(default_factory=dict)


@dataclass
class AnchorStrutResumeItem:
    stage_number: int
    verification_type: int
    basis_cur_step: int
    partial_factor_set: int
    representative_factor: float
    force: float
    anchor_type: int
    anchor_state: int
    changed_to_yielding: int
    calculation_status: int
    name: str


@dataclass
class SupportResumeItem:
    stage_number: int
    verification_type: int
    basis_cur_step: int
    partial_factor_set: int
    representative_factor: float
    force: float
    moment: float
    support_rigidity_type: int
    calculation_status: int
    name: str


@dataclass
class ResultSummary:
    """Samenvatting van maatgevende rekenresultaten per constructiefase."""
    stage_number: int
    max_moment_knm: float       # max abs(moment) uit MOMENTS FORCES DISPLACEMENTS [kNm/m]
    max_shear_kn: float         # max abs(shear) [kN/m]
    max_disp_mm: float          # max abs(disp) × 1000 [mm]
    mob_moment_pct: float       # max(links, rechts) uit SOIL COLLAPSE DATA [%]
    mob_grond_pct: float        # max(links, rechts) uit SOIL COLLAPSE DATA [%]
    ondersteuningen: list[tuple[str, float, float]] = field(default_factory=list)
    # (naam, kracht [kN/m], niveau [m NAP])


@dataclass
class VerifyStepSummary:
    """Resultaat per constructiefase én verificatiestap (vergelijkbaar met D-Sheet overzichtstabel)."""
    stage_number: int
    step_label: str             # bijv. '6.1', '6.5', '6.5 × factor'
    is_ugt: bool
    max_moment_knm: float
    max_shear_kn: float
    max_disp_mm: float | None   # alleen aanwezig als het bestand de waarde bevat
    mob_moment_pct: float | None
    mob_grond_pct: float | None


@dataclass
class FileBundle:
    shd: str = ""


@dataclass
class Project:
    base_name: str
    project_name: str
    file_bundle: FileBundle
    soils: list[Soil] = field(default_factory=list)
    profiles: list[SoilProfile] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    waterlevels: list[WaterLevel] = field(default_factory=list)
    sheet_piling: list[SheetPilingElement] = field(default_factory=list)
    anchors: list[Anchor] = field(default_factory=list)
    struts: list[Strut] = field(default_factory=list)
    spring_supports: list[SpringSupport] = field(default_factory=list)
    rigid_supports: list[RigidSupport] = field(default_factory=list)
    uniform_loads: list[UniformLoad] = field(default_factory=list)
    surcharge_loads: list[SurchargeLoad] = field(default_factory=list)
    horizontal_line_loads: list[HorizontalLineLoad] = field(default_factory=list)
    moments: list[Moment] = field(default_factory=list)
    normal_forces: list[NormalForce] = field(default_factory=list)
    stages: list[Stage] = field(default_factory=list)
    soil_color_map: dict[str, str] = field(default_factory=dict)
    result_steps: dict[str, ResultStep] = field(default_factory=dict)
    anchor_strut_resume: list[AnchorStrutResumeItem] = field(default_factory=list)
    supports_resume: list[SupportResumeItem] = field(default_factory=list)
    result_summaries: list[ResultSummary] = field(default_factory=list)
    verify_step_summaries: list[VerifyStepSummary] = field(default_factory=list)
