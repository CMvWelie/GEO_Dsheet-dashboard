# Renderers

Matplotlib-renderers voor de doorsnede, resultaatgrafieken en aanvullende
berekeningen van het D-Sheet Dashboard. Deze module bevat geen Qt-imports en
werkt uitsluitend met `matplotlib.axes.Axes`-objecten.

## Bestanden

| Bestand | Doel |
|---|---|
| `__init__.py` | Definieert de abstracte basisklasse `BaseRenderer` met de `render()`-methode. |
| `section_renderer.py` | `SectionRenderer` voor de damwand-doorsnede; exporteert ook `y_range_for_project()`, `x_range_for_project()` en `get_stage_profile()` voor `ViewportService`. |
| `output_renderer.py` | `render_output_charts()` voor moment-, dwarskracht- en verplaatsingsgrafieken per bouwfase. |
| `vertical_equilibrium_renderer.py` | Overlay-renderer voor verticaal evenwicht met `VerticalEquilibriumContext`. |
| `draw_helpers.py` | Lage-niveau tekenhulpfuncties (polygonen, pijlen, arceringen) die elke renderer kan hergebruiken. |

## BaseRenderer-contract

Elke renderer subklasseert `renderers.BaseRenderer` en implementeert:

```python
def render(
    self,
    ax: Axes,
    project: Project,
    stage: Stage | None,
    settings: RenderSettings,
    viewport: ViewportSettings,
) -> None:
```

De renderer tekent uitsluitend op de meegegeven `ax`; alle coördinaten zijn in
data-eenheden (meters NAP / meters horizontaal). Geen Qt-imports.

## Teken-cyclus

De aanroepende laag (`AppController` of een tab) volgt altijd dezelfde volgorde:

```python
ax.cla()
renderer.render(ax, project, stage, settings, viewport)
fig.tight_layout()
canvas.draw()
```

## Nieuwe renderer toevoegen

1. Maak `renderers/<naam>_renderer.py` met een klasse die `BaseRenderer`
   subklasseert.
2. Implementeer `render(ax, project, stage, settings, viewport)`; gebruik
   helpers uit `draw_helpers.py` waar mogelijk.
3. Importeer en instantieer de renderer in de aanroepende controller of tab
   en respecteer de teken-cyclus hierboven.

```python
from renderers import BaseRenderer

class MijnRenderer(BaseRenderer):
    def render(self, ax, project, stage, settings, viewport) -> None:
        # teken op ax
        ...
```
