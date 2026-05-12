"""Tests voor bestandsingest in AppController."""

from __future__ import annotations

from app.controller import AppController
from app.state import AppState


def test_ingest_paths_accepteert_alleen_shd(monkeypatch) -> None:
    """Alleen .shd-bestanden worden als runtime-invoer ingelezen."""
    shd = 'C:\\test\\project.shd'
    shi = 'C:\\test\\project.shi'
    shs = 'C:\\test\\project.shs'
    state = AppState()
    controller = AppController(state)
    monkeypatch.setattr(
        'pathlib.Path.read_text',
        lambda self, encoding, errors: 'FILENAME : C:\\projecten\\project.shd\n',
    )

    ok, msg = controller.ingest_paths([shd, shi, shs])

    assert ok
    assert msg == ''
    assert list(state.raw_files) == ['project.shd']
    assert state.source_paths == [shd]


def test_process_files_negeert_oude_niet_shd_raw_files() -> None:
    """Legacy raw_files met .shi/.shs maken geen lege projecten aan."""
    state = AppState()
    state.raw_files = {
        'project.shi': 'oude shi-data',
        'project.shs': 'oude shs-data',
    }
    controller = AppController(state)

    ok, msg = controller.process_files()

    assert not ok
    assert msg == 'Bestanden konden niet worden gegroepeerd.'
    assert state.projects == {}
