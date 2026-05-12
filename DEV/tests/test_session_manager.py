from __future__ import annotations

from app.session_state import SessionData
from reporting.models import ReportMetadata, ReportItem


def test_session_data_defaults():
    sd = SessionData()
    assert sd.version == 1
    assert sd.source_paths == []
    assert isinstance(sd.report_metadata, ReportMetadata)
    assert sd.report_overrides == {}
    assert sd.report_plan_items == []


def test_session_data_round_trip_dict():
    meta = ReportMetadata(client='DKIB', project_name='Testproject')
    item = ReportItem(id='sec_1', kind='section', caption='Invoer')
    sd = SessionData(
        source_paths=['C:/test/file.shd'],
        report_metadata=meta,
        report_overrides={'blk_1': 'Overschreven tekst'},
        report_plan_items=[item],
    )
    d = sd.to_dict()
    assert d['version'] == 1
    assert d['source_paths'] == ['C:/test/file.shd']
    assert d['report_metadata']['client'] == 'DKIB'
    assert d['report_overrides'] == {'blk_1': 'Overschreven tekst'}
    assert d['report_plan_items'][0]['id'] == 'sec_1'

    sd2 = SessionData.from_dict(d)
    assert sd2.source_paths == ['C:/test/file.shd']
    assert sd2.report_metadata.client == 'DKIB'
    assert sd2.report_overrides == {'blk_1': 'Overschreven tekst'}
    assert sd2.report_plan_items[0].id == 'sec_1'
    assert sd2.report_metadata.project_name == 'Testproject'
    assert sd2.report_plan_items[0].caption == 'Invoer'


import json
from pathlib import Path

import pytest

from app.session_manager import SessionManager


def test_session_manager_opslaan_en_laden(tmp_path: Path):
    manager = SessionManager()
    pad = tmp_path / 'project.dsd'
    sd = SessionData(
        source_paths=['C:/project/damwand.shd'],
        report_overrides={'blk_1': 'Test'},
    )
    succes, bericht = manager.opslaan(pad, sd)
    assert succes, bericht
    assert pad.exists()
    inhoud = json.loads(pad.read_text(encoding='utf-8'))
    assert inhoud['version'] == 1

    sd2, fout = manager.laden(pad)
    assert fout == ''
    assert sd2 is not None
    assert sd2.source_paths == ['C:/project/damwand.shd']
    assert sd2.report_overrides == {'blk_1': 'Test'}


def test_session_manager_laden_ontbrekend_bestand(tmp_path: Path):
    manager = SessionManager()
    sd, fout = manager.laden(tmp_path / 'bestaat_niet.dsd')
    assert sd is None
    assert len(fout) > 0


def test_session_manager_laden_kapot_json(tmp_path: Path):
    manager = SessionManager()
    pad = tmp_path / 'kapot.dsd'
    pad.write_text('GEEN JSON', encoding='utf-8')
    sd, fout = manager.laden(pad)
    assert sd is None
    assert len(fout) > 0
