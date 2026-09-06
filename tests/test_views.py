import io

import pytest

from achecker_gui import views
from achecker_gui.analysis import AnalysisError
from achecker_gui.report import parse_report


@pytest.fixture(autouse=True)
def fake_analysis(monkeypatch, fixture_text):
    """Replace the real (slow) engine call with a fixture-driven stub."""
    calls = {}

    def _run(path, **kwargs):
        calls["path"] = path
        calls["kwargs"] = kwargs
        name = "CVE-2021-34273.out" if "CVE" in path else "T4.out"
        return parse_report(fixture_text(name))

    monkeypatch.setattr(views, "run_analysis", _run)
    return calls


def test_index_lists_samples(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"CVE-2021-34273.code" in resp.data
    assert resp.headers["Cache-Control"] == "no-store"


def test_analyze_sample_renders_finding_and_saves_history(client, store):
    resp = client.post(
        "/upload", data={"sample": "CVE-2021-34273.code"}, headers={"X-Requested-With": "fetch"}
    )
    assert resp.status_code == 200
    assert b"finding--high" in resp.data
    assert b"permalink" in resp.data
    assert len(store.list()) == 1


def test_analyze_uploaded_file(client, fake_analysis):
    data = {"file": (io.BytesIO(b"60606040"), "MyContract.code")}
    resp = client.post("/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert fake_analysis["path"].endswith("MyContract.code")


def test_analyze_without_file_is_an_error(client):
    resp = client.post("/upload", data={}, headers={"X-Requested-With": "fetch"})
    assert resp.status_code == 400
    assert b"No file selected" in resp.data


def test_analysis_error_is_shown_not_raised(client, monkeypatch):
    def _boom(*a, **k):
        raise AnalysisError("Analysis timed out after 300 seconds.")

    monkeypatch.setattr(views, "run_analysis", _boom)
    resp = client.post(
        "/upload", data={"sample": "T4.code"}, headers={"X-Requested-With": "fetch"}
    )
    assert resp.status_code == 200
    assert b"timed out" in resp.data


def test_unknown_sample_rejected(client):
    resp = client.post(
        "/upload", data={"sample": "../../etc/passwd"}, headers={"X-Requested-With": "fetch"}
    )
    assert resp.status_code == 400
    assert b"Unknown sample" in resp.data


def test_history_and_detail_and_downloads(client, store):
    client.post("/upload", data={"sample": "CVE-2021-34273.code"})
    entry = store.list()[0]
    analysis_id = str(entry["_id"])

    history = client.get("/history")
    assert history.status_code == 200
    assert b"CVE-2021-34273.code" in history.data
    assert b"badge--issues" in history.data

    detail = client.get(f"/history/{analysis_id}")
    assert detail.status_code == 200
    assert b"transferOwnership(address)" in detail.data

    as_json = client.get(f"/history/{analysis_id}/download.json")
    assert as_json.status_code == 200
    assert as_json.headers["Content-Disposition"].endswith('.json"')

    as_md = client.get(f"/history/{analysis_id}/download.md")
    assert as_md.status_code == 200
    assert b"# AChecker report" in as_md.data


def test_history_detail_missing_id_is_404(client):
    assert client.get("/history/6a9dd02e03409dff8f3d2001").status_code == 404


def test_legacy_view_uploads_redirects(client):
    resp = client.get("/view-uploads")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/history")


def test_history_unavailable_when_store_down(app, monkeypatch):
    monkeypatch.setattr(app.extensions["history_store"], "list", lambda *a, **k: None)
    resp = app.test_client().get("/history")
    assert b"not reachable" in resp.data
