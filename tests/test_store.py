import mongomock
import pytest

from achecker_gui.report import parse_report
from achecker_gui.store import HistoryStore


@pytest.fixture
def store():
    return HistoryStore(None, None, collection=mongomock.MongoClient().db.col)


def test_save_and_get_roundtrip(store, fixture_text):
    report = parse_report(fixture_text("CVE-2021-34273.out"))
    analysis_id = store.save("CVE-2021-34273.code", report)

    assert analysis_id
    doc = store.get(analysis_id)
    assert doc["filename"] == "CVE-2021-34273.code"
    assert doc["issue_count"] == 1
    assert doc["findings"][0]["function"] == "transferOwnership(address)"
    assert doc["upload_time"].endswith(("AM", "PM"))


def test_list_is_newest_first(store):
    store.save("a.code", parse_report(""))
    store.save("b.code", parse_report(""))
    names = [d["filename"] for d in store.list()]
    assert names == ["b.code", "a.code"]


def test_get_with_bad_id_returns_none(store):
    assert store.get("not-an-objectid") is None
    assert store.get(None) is None


class _BrokenCollection:
    """Every operation raises, like an unreachable MongoDB."""

    @property
    def database(self):
        raise _err()

    def insert_one(self, *a, **k):
        raise _err()

    def find(self, *a, **k):
        raise _err()

    def find_one(self, *a, **k):
        raise _err()


def _err():
    from pymongo.errors import ServerSelectionTimeoutError

    return ServerSelectionTimeoutError("no server")


def test_store_degrades_when_db_unavailable():
    store = HistoryStore(None, None, collection=_BrokenCollection())
    assert store.save("x.code", parse_report("")) is None
    assert store.list() is None
    assert store.get("6a9dd02e03409dff8f3d2001") is None
    assert store.available() is False
