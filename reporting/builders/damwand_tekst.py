"""Vaste rapportageteksten voor het damwandhoofdstuk."""

from __future__ import annotations


DAMWAND_INTRO_TEKST = (
    'Voor de grondkering zijn de volgende eigenschappen aangehouden.'
)

DAMWAND_TOELICHTING_REGELS = [
    ('EI', 'de ongereduceerde buigstijfheid van de doorsnede'),
    ('Wy;el', 'het ongereduceerde weerstandsmoment van de doorsnede'),
    ('M', 'het ongereduceerde opneembare moment van de doorsnede'),
]

FASERING_TITEL = 'Fasering'
FASERING_INTRO_TEKST = 'De onderstaande fasering is als volgt toegepast.'
FASERING_TABEL_INTRO_TEKST = (
    'Voor de grafisch weergegeven bouwfasering(en) zie de onderstaande tabel.'
)

RESULTATEN_TITEL = 'Resultaten'
RESULTATEN_INTRO_TEKST = (
    'In deze tabel zijn de belangrijkste gegevens en maatgevende projectresultaten '
    'samengevat. De resultaatwaarden betreffen de maxima over de beschikbare fases '
    'en verificatiestappen volgens de CUR166.'
)
RESULTATEN_GRAFIEK_INTRO_TEKST = (
    'Voor de grafische weergave van de maatgevende resultaten zie hiervoor '
    'onderstaande tabel:'
)


def damwand_toelichting_tekst() -> str:
    """Geef de toelichting op de damwandtabel als meerregelige tekst.

    Returns
    -------
    str
        Toelichting met de betekenis van EI, Wy;el en M.
    """
    regels = ['Hierin is:']
    regels.extend(
        f'{symbool}\t{omschrijving}'
        for symbool, omschrijving in DAMWAND_TOELICHTING_REGELS
    )
    return '\n'.join(regels)


def faseringsregels(fase_namen: list[str]) -> list[str]:
    """Geef de faselijst voor de rapportage.

    Parameters
    ----------
    fase_namen:
        Namen van de beschikbare constructiefases.

    Returns
    -------
    list[str]
        Regels in de vorm ``- Fase n: Naam``.
    """
    return [
        f'- Fase {index}: {fase_naam}'
        for index, fase_naam in enumerate(fase_namen, start=1)
    ]


def project_fase_namen(project: object | None) -> list[str]:
    """Geef alle bekende fasenamen uit invoer en .shd-resultaten.

    Parameters
    ----------
    project:
        Project-object met invoerfases en optionele resultaatdata.

    Returns
    -------
    list[str]
        Namen in fasevolgorde. Fases die alleen als nummer in de .shd voorkomen
        krijgen de naam ``Fase n``.
    """
    if project is None:
        return []

    stages = getattr(project, 'stages', None) or []
    namen_by_num: dict[int, str] = {
        index: getattr(stage, 'name', '') or f'Fase {index}'
        for index, stage in enumerate(stages, start=1)
    }
    fase_nummers: set[int] = set(namen_by_num)

    for summary in getattr(project, 'result_summaries', None) or []:
        fase_nummers.add(getattr(summary, 'stage_number', 0))
    for summary in getattr(project, 'verify_step_summaries', None) or []:
        fase_nummers.add(getattr(summary, 'stage_number', 0))
    for step in (getattr(project, 'result_steps', None) or {}).values():
        fase_nummers.update((getattr(step, 'stages', None) or {}).keys())

    return [
        namen_by_num.get(fase_nummer, f'Fase {fase_nummer}')
        for fase_nummer in sorted(n for n in fase_nummers if n > 0)
    ]
