"""Subtab Verticaal evenwicht — opbarstcontrole conform NEN 9997-1:2025 §10.2."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QGroupBox, QGridLayout, QComboBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.settings import RenderSettings, ViewportSettings
from parsers.models import Project, Surface, Stage
from renderers.vertical_equilibrium_renderer import (
    VerticalEquilibriumContext,
    VerticalEquilibriumRenderer,
)
from utils.formatting import fmt_number

_MATERIAALFACTOR_STANDAARD = 0.9
_WATERGEWICHT_STANDAARD = 10.0


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
    bodem_punten_raw: list[dict] = field(default_factory=list)
    # ruwe bodempunten {'nr', 'x', 'y'} uit de surface — voor debugdoeleinden
    waterpeil_bouwput_naam: str = ''
    # naam van het waterpeil zoals gevonden in de stage — voor debugdoeleinden


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

    # Waterpeil in bouwput: zijde-afhankelijk uit de gekozen fase.
    _wl_map = {wl.name: wl for wl in project.waterlevels}
    _water_naam_bouwput = (
        (stage.left_water if profiel_zijde == 'links' else stage.right_water)
        if stage else None
    ) or ''
    _bouwput_obj = _wl_map.get(_water_naam_bouwput)
    water_naam = _water_naam_bouwput
    waterpeil_bouwput: float | None = _bouwput_obj.level if _bouwput_obj else stijghoogte

    surf_links_naam = stage.left_surface if stage else None
    surf_rechts_naam = stage.right_surface if stage else None
    surf_links = _find_surface(surf_links_naam) if surf_links_naam else None
    surf_rechts = _find_surface(surf_rechts_naam) if surf_rechts_naam else None

    ref_surf = surf_links if profiel_zijde == 'links' else surf_rechts
    breedte = None
    ontgravingsniveau = None
    bodem_punten_raw: list[dict] = []
    if ref_surf and ref_surf.points:
        x_l, x_r, min_y = _zoek_bodem_punten(ref_surf)
        breedte = abs(x_r - x_l)
        ontgravingsniveau = min_y
        bodem_punten_raw = [pt for pt in ref_surf.points if abs(pt['y'] - min_y) <= 0.01]

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
        waterpeil_bouwput=waterpeil_bouwput,
        grondlagen=grondlagen,
        talud_links=talud_links,
        talud_rechts=talud_rechts,
        bodem_punten_raw=bodem_punten_raw,
        waterpeil_bouwput_naam=water_naam,
    )


class TabVerticaalEvenwicht(QWidget):
    """Subtab met verticaal-evenwichtcontrole (opbarsten, NEN 9997-1:2025 §10.2)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project: Project | None = None
        self._auto_waarden: AutoWaardenVE | None = None
        self._laatste_project_naam: str | None = None
        self._ve_renderer = VerticalEquilibriumRenderer()
        self._build()

    # ------------------------------------------------------------------
    # Opbouw
    # ------------------------------------------------------------------
    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        linker_paneel = QWidget()
        linker_layout = QVBoxLayout(linker_paneel)
        linker_layout.setContentsMargins(0, 0, 0, 0)
        linker_layout.setSpacing(12)
        linker_layout.addWidget(self._bouw_instellingen_groep())
        linker_layout.addWidget(self._bouw_invoer_groep())
        linker_layout.addWidget(self._bouw_resultaat_groep())
        linker_layout.addWidget(self._bouw_spanningsopbouw_groep(), stretch=1)

        linker_scroll = QScrollArea()
        linker_scroll.setWidgetResizable(True)
        linker_scroll.setFrameShape(QFrame.Shape.NoFrame)
        linker_scroll.setWidget(linker_paneel)

        layout.addWidget(linker_scroll, stretch=1)
        layout.addWidget(self._bouw_visualisatie_groep(), stretch=1)
        self._verbind_signalen()
        self._herbereken()

    def _bouw_visualisatie_groep(self) -> QGroupBox:
        groep = QGroupBox('Visualisatie')
        lay = QVBoxLayout(groep)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        self._ve_fig = Figure(figsize=(12, 5), dpi=96)
        self._ve_ax = self._ve_fig.add_subplot(111)
        self._ve_canvas = FigureCanvas(self._ve_fig)
        self._ve_canvas.setMinimumHeight(320)
        self._ve_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        lay.addWidget(self._ve_canvas)
        return groep

    def _bouw_instellingen_groep(self) -> QGroupBox:
        groep = QGroupBox('Projectinstellingen')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._combo_stage = QComboBox()
        self._combo_profiel = QComboBox()
        self._combo_profiel.addItems(['Links', 'Rechts'])
        self._combo_evenwicht = QComboBox()

        grid.addWidget(QLabel('Stage'), 0, 0)
        grid.addWidget(self._combo_stage, 0, 1)
        grid.addWidget(QLabel('Grondprofiel'), 1, 0)
        grid.addWidget(self._combo_profiel, 1, 1)
        grid.addWidget(QLabel('Evenwichtsniveau-laag (o.k.)'), 2, 0)
        grid.addWidget(self._combo_evenwicht, 2, 1)
        return groep

    def _bouw_invoer_groep(self) -> QGroupBox:
        groep = QGroupBox('Invoer')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._spin_ontgraving      = self._maak_spin(-50.0, 50.0, 2)
        self._spin_waterpeil       = self._maak_spin(-50.0, 50.0, 2)
        self._spin_stijghoogte     = self._maak_spin(-50.0, 50.0, 2)
        self._spin_materiaalfactor = self._maak_spin(0.0, 2.0, 2)
        self._spin_watergewicht    = self._maak_spin(0.0, 20.0, 1)
        self._spin_materiaalfactor.setValue(_MATERIAALFACTOR_STANDAARD)
        self._spin_watergewicht.setValue(_WATERGEWICHT_STANDAARD)

        self._btn_reset_ontgraving  = self._maak_reset_knop()
        self._btn_reset_waterpeil   = self._maak_reset_knop()
        self._btn_reset_stijghoogte = self._maak_reset_knop()

        rij = 0
        for label, spin, reset in [
            ('Ontgravingsniveau (m NAP)',    self._spin_ontgraving,      self._btn_reset_ontgraving),
            ('Waterpeil in bouwput (m NAP)', self._spin_waterpeil,       self._btn_reset_waterpeil),
            ('Stijghoogte w.v.p. (m NAP)',   self._spin_stijghoogte,     self._btn_reset_stijghoogte),
            ('Materiaalfactor \u03b3G;stb (\u2013)',   self._spin_materiaalfactor, None),
            ('Watergewicht \u03b3_w (kN/m\u00b3)',     self._spin_watergewicht,    None),
        ]:
            grid.addWidget(QLabel(label), rij, 0)
            grid.addWidget(spin, rij, 1)
            if reset:
                grid.addWidget(reset, rij, 2)
            rij += 1

        self._chk_taludinvloed = QCheckBox('Taludinvloed meenemen')
        grid.addWidget(self._chk_taludinvloed, rij, 0, 1, 3)
        rij += 1

        self._widget_talud = QWidget()
        tgrid = QGridLayout(self._widget_talud)
        tgrid.setContentsMargins(0, 0, 0, 0)
        tgrid.setSpacing(6)

        self._spin_breedte          = self._maak_spin(0.0, 500.0, 2)
        self._spin_maaiveld_links   = self._maak_spin(-20.0, 20.0, 2)
        self._spin_helling_links_v  = self._maak_spin(0.0, 10.0, 1)
        self._spin_helling_links_h  = self._maak_spin(0.0, 100.0, 1)
        self._spin_maaiveld_rechts  = self._maak_spin(-20.0, 20.0, 2)
        self._spin_helling_rechts_v = self._maak_spin(0.0, 10.0, 1)
        self._spin_helling_rechts_h = self._maak_spin(0.0, 100.0, 1)

        self._btn_reset_breedte      = self._maak_reset_knop()
        self._btn_reset_talud_links  = self._maak_reset_knop()
        self._btn_reset_talud_rechts = self._maak_reset_knop()

        tgrid.addWidget(QLabel('Breedte bouwputbodem (m)'), 0, 0)
        tgrid.addWidget(self._spin_breedte, 0, 1, 1, 3)
        tgrid.addWidget(self._btn_reset_breedte, 0, 4)

        tgrid.addWidget(QLabel('Maaiveld links (m NAP)'), 1, 0)
        tgrid.addWidget(self._spin_maaiveld_links, 1, 1, 1, 3)

        tgrid.addWidget(QLabel('Helling links v : h'), 2, 0)
        tgrid.addWidget(self._spin_helling_links_v, 2, 1)
        tgrid.addWidget(QLabel(':'), 2, 2)
        tgrid.addWidget(self._spin_helling_links_h, 2, 3)
        tgrid.addWidget(self._btn_reset_talud_links, 2, 4)

        tgrid.addWidget(QLabel('Maaiveld rechts (m NAP)'), 3, 0)
        tgrid.addWidget(self._spin_maaiveld_rechts, 3, 1, 1, 3)

        tgrid.addWidget(QLabel('Helling rechts v : h'), 4, 0)
        tgrid.addWidget(self._spin_helling_rechts_v, 4, 1)
        tgrid.addWidget(QLabel(':'), 4, 2)
        tgrid.addWidget(self._spin_helling_rechts_h, 4, 3)
        tgrid.addWidget(self._btn_reset_talud_rechts, 4, 4)

        self._widget_talud.setVisible(False)
        grid.addWidget(self._widget_talud, rij, 0, 1, 3)
        return groep

    def _bouw_resultaat_groep(self) -> QGroupBox:
        groep = QGroupBox('Resultaat')
        grid = QGridLayout(groep)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        self._lbl_gstb     = QLabel('-')
        self._lbl_vdst     = QLabel('-')
        self._lbl_uc_basis = QLabel('-')
        self._lbl_uc_talud = QLabel('-')
        self._lbl_status   = QLabel('-')

        font_groot = QFont()
        font_groot.setPointSize(14)
        font_groot.setBold(True)
        self._lbl_uc_basis.setFont(font_groot)
        self._lbl_uc_talud.setFont(font_groot)
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setMinimumHeight(44)

        self._lbl_uc_talud_label = QLabel('UC (met taludinvloed)')
        grid.addWidget(QLabel('Gstb;d'), 0, 0)
        grid.addWidget(self._lbl_gstb, 0, 1)
        grid.addWidget(QLabel('Vdst;d'), 1, 0)
        grid.addWidget(self._lbl_vdst, 1, 1)
        grid.addWidget(QLabel('UC (zonder taludinvloed)'), 2, 0)
        grid.addWidget(self._lbl_uc_basis, 2, 1)
        grid.addWidget(self._lbl_uc_talud_label, 3, 0)
        grid.addWidget(self._lbl_uc_talud, 3, 1)
        grid.addWidget(self._lbl_status, 4, 0, 1, 2)

        self._lbl_uc_talud_label.setVisible(False)
        self._lbl_uc_talud.setVisible(False)
        return groep

    def _bouw_spanningsopbouw_groep(self) -> QGroupBox:
        groep = QGroupBox('Spanningsopbouw Gstb;d')
        lay = QVBoxLayout(groep)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)

        kolommen = [
            'Laag', 'b.k. eff.\n(m NAP)', 'o.k. eff.\n(m NAP)',
            'Dikte droog\n(m)', 'Dikte nat\n(m)',
            '\u03b3_dr\n(kN/m\u00b3)', '\u03b3_nat\n(kN/m\u00b3)',
            'Bijdrage\n(kN/m\u00b2)',
        ]
        self._tabel_spanning = QTableWidget(0, len(kolommen))
        self._tabel_spanning.setHorizontalHeaderLabels(kolommen)
        self._tabel_spanning.verticalHeader().setVisible(False)
        self._tabel_spanning.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabel_spanning.setAlternatingRowColors(True)
        header = self._tabel_spanning.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(kolommen)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        lay.addWidget(self._tabel_spanning)
        return groep

    def _maak_spin(self, minimum: float, maximum: float, decimalen: int) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimalen)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(110)
        return spin

    def _maak_reset_knop(self) -> QPushButton:
        btn = QPushButton('\u21ba')
        btn.setFixedWidth(30)
        btn.setToolTip('Terugzetten naar projectwaarde')
        return btn

    # ------------------------------------------------------------------
    # Signalen
    # ------------------------------------------------------------------
    def _verbind_signalen(self) -> None:
        for spin in [
            self._spin_ontgraving, self._spin_waterpeil, self._spin_stijghoogte,
            self._spin_materiaalfactor, self._spin_watergewicht,
            self._spin_breedte,
            self._spin_maaiveld_links, self._spin_helling_links_v, self._spin_helling_links_h,
            self._spin_maaiveld_rechts, self._spin_helling_rechts_v, self._spin_helling_rechts_h,
        ]:
            spin.valueChanged.connect(self._herbereken)

        self._combo_stage.currentTextChanged.connect(self._on_stage_gewijzigd)
        self._combo_profiel.currentTextChanged.connect(self._on_profiel_gewijzigd)
        self._combo_evenwicht.currentTextChanged.connect(self._herbereken)
        self._chk_taludinvloed.toggled.connect(self._on_talud_toggled)

        self._btn_reset_ontgraving.clicked.connect(self._reset_ontgraving)
        self._btn_reset_waterpeil.clicked.connect(self._reset_waterpeil)
        self._btn_reset_stijghoogte.clicked.connect(self._reset_stijghoogte)
        self._btn_reset_breedte.clicked.connect(self._reset_breedte)
        self._btn_reset_talud_links.clicked.connect(self._reset_talud_links)
        self._btn_reset_talud_rechts.clicked.connect(self._reset_talud_rechts)

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------
    def update_project(self, project: Project | None) -> None:
        """Vul invoervelden automatisch in vanuit project.

        Parameters
        ----------
        project:
            Actief project, of None als geen project geladen.
        """
        nieuwe_naam = project.base_name if project else None
        if nieuwe_naam == self._laatste_project_naam:
            return
        self._laatste_project_naam = nieuwe_naam
        self._project = project
        self._auto_waarden = None

        self._combo_stage.blockSignals(True)
        self._combo_stage.clear()
        if project:
            for stage in project.stages:
                self._combo_stage.addItem(stage.name)
        self._combo_stage.blockSignals(False)

        self._laad_auto_waarden()

    # ------------------------------------------------------------------
    # Interne state-handlers
    # ------------------------------------------------------------------
    def _laad_auto_waarden(self) -> None:
        """Laad auto-waarden voor de huidige stage- en profielkeuze."""
        if not self._project or not self._project.stages:
            self._auto_waarden = None
            self._vul_evenwicht_combo()
            self._render_visualisatie()
            return

        stage_naam = self._combo_stage.currentText()
        profiel_zijde = 'links' if self._combo_profiel.currentIndex() == 0 else 'rechts'
        self._auto_waarden = extraheer_auto_waarden_ve(
            self._project, stage_naam, profiel_zijde
        )
        self._vul_evenwicht_combo()
        self._reset_ontgraving()
        self._reset_waterpeil()
        self._reset_stijghoogte()
        self._reset_breedte()
        self._reset_talud_links()
        self._reset_talud_rechts()
        self._render_visualisatie()

    def _vul_evenwicht_combo(self) -> None:
        """Vul de evenwichtsniveau-dropdown met genummerde laagnamen uit het grondprofiel."""
        self._combo_evenwicht.blockSignals(True)
        huidig_idx = self._combo_evenwicht.currentIndex()
        self._combo_evenwicht.clear()
        if self._auto_waarden:
            for i, (naam, _bk, _ok, _gdr, _gnat) in enumerate(self._auto_waarden.grondlagen):
                self._combo_evenwicht.addItem(f'{i + 1} \u2013 {naam}')
            if 0 <= huidig_idx < self._combo_evenwicht.count():
                self._combo_evenwicht.setCurrentIndex(huidig_idx)
        self._combo_evenwicht.blockSignals(False)

    def _on_stage_gewijzigd(self) -> None:
        self._laad_auto_waarden()

    def _on_profiel_gewijzigd(self) -> None:
        self._laad_auto_waarden()

    def _on_talud_toggled(self, aan: bool) -> None:
        self._widget_talud.setVisible(aan)
        self._lbl_uc_talud_label.setVisible(aan)
        self._lbl_uc_talud.setVisible(aan)
        self._herbereken()

    # ------------------------------------------------------------------
    # Reset-handlers
    # ------------------------------------------------------------------
    def _reset_ontgraving(self) -> None:
        if self._auto_waarden and self._auto_waarden.ontgravingsniveau is not None:
            self._spin_ontgraving.blockSignals(True)
            self._spin_ontgraving.setValue(self._auto_waarden.ontgravingsniveau)
            self._spin_ontgraving.blockSignals(False)
            punten = self._auto_waarden.bodem_punten_raw
            if punten:
                regels = '\n'.join(
                    f"  punt {pt['nr']}: x = {pt['x']:.4f} m,  y = {pt['y']:.4f} m NAP"
                    for pt in punten
                )
                self._spin_ontgraving.setToolTip(
                    f"Bodempunten uit surface ({len(punten)} punt(en)):\n{regels}"
                )
            else:
                self._spin_ontgraving.setToolTip('')
        self._herbereken()

    def _reset_waterpeil(self) -> None:
        if self._auto_waarden and self._auto_waarden.waterpeil_bouwput is not None:
            self._spin_waterpeil.blockSignals(True)
            self._spin_waterpeil.setValue(self._auto_waarden.waterpeil_bouwput)
            self._spin_waterpeil.blockSignals(False)
            regels = [f"Waterpeilnaam uit stage: '{self._auto_waarden.waterpeil_bouwput_naam}'"]
            if self._project and self._project.waterlevels:
                regels.append('\nBeschikbare waterpeilen in project:')
                for wl in self._project.waterlevels:
                    regels.append(f"  \u2013 {wl.name}: {fmt_number(wl.level, 2)} m NAP")
            self._spin_waterpeil.setToolTip('\n'.join(regels))
        self._herbereken()

    def _reset_stijghoogte(self) -> None:
        if self._auto_waarden and self._auto_waarden.stijghoogte is not None:
            self._spin_stijghoogte.blockSignals(True)
            self._spin_stijghoogte.setValue(self._auto_waarden.stijghoogte)
            self._spin_stijghoogte.blockSignals(False)
        self._herbereken()

    def _reset_breedte(self) -> None:
        if self._auto_waarden and self._auto_waarden.breedte_bouwputbodem is not None:
            self._spin_breedte.blockSignals(True)
            self._spin_breedte.setValue(self._auto_waarden.breedte_bouwputbodem)
            self._spin_breedte.blockSignals(False)
        self._herbereken()

    def _reset_talud_links(self) -> None:
        if self._auto_waarden and self._auto_waarden.talud_links is not None:
            tl = self._auto_waarden.talud_links
            for spin, val in [
                (self._spin_maaiveld_links,  tl.maaiveld_niveau),
                (self._spin_helling_links_v, 1.0),
                (self._spin_helling_links_h, tl.helling_h_per_v),
            ]:
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self._herbereken()

    def _reset_talud_rechts(self) -> None:
        if self._auto_waarden and self._auto_waarden.talud_rechts is not None:
            tr = self._auto_waarden.talud_rechts
            for spin, val in [
                (self._spin_maaiveld_rechts,  tr.maaiveld_niveau),
                (self._spin_helling_rechts_v, 1.0),
                (self._spin_helling_rechts_h, tr.helling_h_per_v),
            ]:
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)
        self._herbereken()

    # ------------------------------------------------------------------
    # Berekening
    # ------------------------------------------------------------------
    def _evenwichtsniveau(self) -> float | None:
        """Lees de o.k. van de gekozen evenwichtsniveau-laag via index."""
        if not self._auto_waarden:
            return None
        idx = self._combo_evenwicht.currentIndex()
        if 0 <= idx < len(self._auto_waarden.grondlagen):
            return self._auto_waarden.grondlagen[idx][2]
        return None

    def _huidige_stage(self) -> Stage | None:
        """Geef de in dit subtabblad gekozen stage terug."""
        if not self._project:
            return None
        naam = self._combo_stage.currentText()
        return next((stage for stage in self._project.stages if stage.name == naam), None)

    def _render_visualisatie(self) -> None:
        """Render de verticaal-evenwichtvisualisatie."""
        ax = self._ve_ax
        if not self._project:
            ax.cla()
            ax.set_facecolor('white')
            ax.text(
                0.5, 0.5, 'Geen project geladen',
                transform=ax.transAxes, ha='center', va='center',
                fontsize=12, color='#888888',
            )
            ax.axis('off')
            self._ve_canvas.draw()
            return

        self._ve_renderer.set_context(self._render_context())
        self._ve_renderer.render(
            ax=ax,
            project=self._project,
            stage=self._huidige_stage(),
            settings=RenderSettings(),
            viewport=ViewportSettings(auto=True),
        )
        self._ve_fig.tight_layout()
        self._ve_canvas.draw()

    def _render_context(self) -> VerticalEquilibriumContext:
        """Maak de renderer-context uit de actuele UI-waarden."""
        lagen = self._auto_waarden.grondlagen if self._auto_waarden else []
        return VerticalEquilibriumContext(
            profiel_zijde='links' if self._combo_profiel.currentIndex() == 0 else 'rechts',
            ontgravingsniveau=self._spin_ontgraving.value(),
            waterpeil_bouwput=self._spin_waterpeil.value(),
            stijghoogte=self._spin_stijghoogte.value(),
            watergewicht=self._spin_watergewicht.value(),
            evenwichtsniveau=self._evenwichtsniveau(),
            grondlagen=lagen,
        )

    def _herbereken(self) -> None:
        lagen = self._auto_waarden.grondlagen if self._auto_waarden else []
        evenwichtsniveau = self._evenwichtsniveau()

        if not lagen or evenwichtsniveau is None:
            self._lbl_gstb.setText('-')
            self._lbl_vdst.setText('-')
            self._lbl_uc_basis.setText('-')
            self._lbl_uc_talud.setText('-')
            self._wis_spanning_tabel()
            self._toon_status_neutraal()
            self._render_visualisatie()
            return

        ontgravingsniveau = self._spin_ontgraving.value()
        waterpeil_bouwput = self._spin_waterpeil.value()
        stijghoogte       = self._spin_stijghoogte.value()
        materiaalfactor   = self._spin_materiaalfactor.value()
        watergewicht      = self._spin_watergewicht.value()

        gstb, vdst, uc = bereken_verticaal_evenwicht(
            lagen=lagen,
            ontgravingsniveau=ontgravingsniveau,
            waterpeil_bouwput=waterpeil_bouwput,
            stijghoogte=stijghoogte,
            evenwichtsniveau=evenwichtsniveau,
            materiaalfactor=materiaalfactor,
            watergewicht=watergewicht,
        )

        self._vul_spanning_tabel(
            lagen=lagen,
            ontgravingsniveau=ontgravingsniveau,
            waterpeil_bouwput=waterpeil_bouwput,
            stijghoogte=stijghoogte,
            evenwichtsniveau=evenwichtsniveau,
            materiaalfactor=materiaalfactor,
            watergewicht=watergewicht,
        )

        self._lbl_gstb.setText(f'{fmt_number(gstb, 2)} kN/m\u00b2')
        self._lbl_vdst.setText(f'{fmt_number(vdst, 2)} kN/m\u00b2')
        self._lbl_uc_basis.setText(
            fmt_number(uc, 3) if not math.isinf(uc) else '\u221e'
        )

        uc_maatgevend = uc
        if self._chk_taludinvloed.isChecked() and not math.isinf(vdst) and vdst > 0.0:
            b = self._spin_breedte.value() / 2.0
            d2 = abs(ontgravingsniveau - evenwichtsniveau)
            bijdragen: list[float] = []
            for maaiveld_spin, v_spin, h_spin in [
                (self._spin_maaiveld_links,  self._spin_helling_links_v,  self._spin_helling_links_h),
                (self._spin_maaiveld_rechts, self._spin_helling_rechts_v, self._spin_helling_rechts_h),
            ]:
                v = v_spin.value()
                h = h_spin.value()
                if v <= 0.0 or h <= 0.0:
                    continue
                maaiveld = maaiveld_spin.value()
                d1 = maaiveld - ontgravingsniveau
                if d1 <= 0.0:
                    continue
                a = d1 * (h / v)
                f = bereken_taludinvloed(d1, a, b, d2)
                gewicht = bereken_gewicht_talud(lagen, maaiveld, ontgravingsniveau)
                bijdragen.append(f * gewicht)
            if bijdragen:
                gstb_met = gstb + min(bijdragen)
                uc_met = gstb_met / vdst
                self._lbl_uc_talud.setText(fmt_number(uc_met, 3))
                uc_maatgevend = uc_met
            else:
                self._lbl_uc_talud.setText('-')

        self._toon_status(uc_maatgevend, vdst)
        self._render_visualisatie()

    def _wis_spanning_tabel(self) -> None:
        self._tabel_spanning.setRowCount(0)

    def _vul_spanning_tabel(
        self,
        lagen: list[tuple[str, float, float, float, float]],
        ontgravingsniveau: float,
        waterpeil_bouwput: float,
        stijghoogte: float,
        evenwichtsniveau: float,
        materiaalfactor: float,
        watergewicht: float,
    ) -> None:
        """Vul de spanningsopbouw-tabel met laag-voor-laag bijdragen aan Gstb;d."""
        tabel = self._tabel_spanning
        tabel.setRowCount(0)

        def _cel(tekst: str, rechts: bool = False) -> QTableWidgetItem:
            item = QTableWidgetItem(tekst)
            if rechts:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return item

        totaal = 0.0
        for naam, bk, ok, gamma_dr, gamma_nat in lagen:
            eff_bk = min(bk, ontgravingsniveau)
            eff_ok = max(ok, evenwichtsniveau)
            if eff_bk <= eff_ok:
                continue
            dikte_droog = max(0.0, eff_bk - max(eff_ok, waterpeil_bouwput))
            dikte_nat   = max(0.0, min(eff_bk, waterpeil_bouwput) - eff_ok)
            bijdrage = (dikte_droog * gamma_dr + dikte_nat * gamma_nat) * materiaalfactor
            totaal += bijdrage

            rij = tabel.rowCount()
            tabel.insertRow(rij)
            tabel.setItem(rij, 0, _cel(naam))
            tabel.setItem(rij, 1, _cel(fmt_number(eff_bk, 2), True))
            tabel.setItem(rij, 2, _cel(fmt_number(eff_ok, 2), True))
            tabel.setItem(rij, 3, _cel(fmt_number(dikte_droog, 2), True))
            tabel.setItem(rij, 4, _cel(fmt_number(dikte_nat,   2), True))
            tabel.setItem(rij, 5, _cel(fmt_number(gamma_dr,    1), True))
            tabel.setItem(rij, 6, _cel(fmt_number(gamma_nat,   1), True))
            tabel.setItem(rij, 7, _cel(fmt_number(bijdrage,    2), True))

        # Totaalrij Gstb;d
        rij = tabel.rowCount()
        tabel.insertRow(rij)
        tabel.setItem(rij, 0, _cel('Gstb;d (totaal)'))
        tabel.setItem(rij, 7, _cel(fmt_number(totaal, 2), True))
        font_bold = tabel.item(rij, 0).font()
        font_bold.setBold(True)
        for col in range(tabel.columnCount()):
            item = tabel.item(rij, col)
            if item:
                item.setFont(font_bold)

        # Vdst;d-rij
        vdst = max(0.0, (stijghoogte - evenwichtsniveau) * watergewicht)
        rij = tabel.rowCount()
        tabel.insertRow(rij)
        tabel.setItem(rij, 0, _cel(
            f'Vdst;d = ({fmt_number(stijghoogte, 2)} \u2212 {fmt_number(evenwichtsniveau, 2)}) \u00d7 {fmt_number(watergewicht, 1)}'
        ))
        tabel.setItem(rij, 7, _cel(fmt_number(vdst, 2), True))
        for col in range(tabel.columnCount()):
            item = tabel.item(rij, col)
            if item:
                item.setFont(font_bold)

    def _toon_status_neutraal(self) -> None:
        self._lbl_status.setText('\u2013')
        self._lbl_status.setStyleSheet(
            'background-color: #78909c; color: white; font-weight: bold;'
            ' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )

    def _toon_status(self, uc: float, vdst: float) -> None:
        if math.isinf(uc):
            self._lbl_status.setText('GEEN WATERDRUK')
            self._lbl_status.setStyleSheet(
                'background-color: #78909c; color: white; font-weight: bold;'
                ' font-size: 14pt; border-radius: 4px; padding: 4px;'
            )
            return
        voldoet = uc >= 1.0
        tekst = 'VOLDOET' if voldoet else 'VOLDOET NIET'
        kleur = '#2e7d32' if voldoet else '#c62828'
        self._lbl_status.setText(tekst)
        self._lbl_status.setStyleSheet(
            f'background-color: {kleur}; color: white; font-weight: bold;'
            f' font-size: 14pt; border-radius: 4px; padding: 4px;'
        )
