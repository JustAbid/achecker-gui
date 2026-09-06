import pathlib

import mongomock
import pytest

from achecker_gui import create_app
from achecker_gui.store import HistoryStore

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    def _load(name):
        return (FIXTURES / name).read_text()

    return _load


@pytest.fixture
def store():
    collection = mongomock.MongoClient().db.uploaded_files
    return HistoryStore(None, None, collection=collection)


@pytest.fixture
def app(store):
    return create_app({"TESTING": True, "WTF_CSRF_ENABLED": False}, store=store)


@pytest.fixture
def client(app):
    return app.test_client()
