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
