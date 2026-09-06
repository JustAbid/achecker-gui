"""Routes for the AChecker web interface."""

import json
import os

from flask import (
    Blueprint,
    Response,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from .analysis import AnalysisError, run_analysis
from .reporting import report_to_markdown

bp = Blueprint("main", __name__)

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")


def _store():
    return current_app.extensions["history_store"]


def _wants_fragment():
    return request.headers.get("X-Requested-With") == "fetch"


def _render_results(result, status=200):
    template = "_results.html" if _wants_fragment() else "index.html"
    return render_template(template, result=result), status


@bp.route("/")
def index():
    return render_template("index.html", result=None, samples=_sample_names())


@bp.route("/upload", methods=["POST"])
def upload():
    uploaded = request.files.get("file")
    sample = request.form.get("sample")

    if sample:
        path = _safe_sample_path(sample)
        if path is None:
            return _render_results({"error": "Unknown sample."}, status=400)
        filename = os.path.basename(path)
    elif uploaded and uploaded.filename:
        filename = secure_filename(uploaded.filename)
        if not filename:
            return _render_results({"error": "Invalid file name."}, status=400)
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        uploaded.save(path)
    else:
        return _render_results({"error": "No file selected."}, status=400)

    try:
        report = run_analysis(
            path,
            timeout=current_app.config["ANALYSIS_TIMEOUT"],
            memory_gb=current_app.config["ANALYSIS_MEMORY_GB"],
        )
    except AnalysisError as exc:
        return _render_results({"error": str(exc)}, status=200)

    analysis_id = _store().save(filename, report)
    result = report.to_dict()
    result["filename"] = filename
    result["analysis_id"] = analysis_id
    return _render_results(result)


@bp.route("/history")
def history():
    entries = _store().list()
    return render_template("history.html", entries=entries)


@bp.route("/history/<analysis_id>")
def history_detail(analysis_id):
    doc = _store().get(analysis_id)
    if doc is None:
        return render_template("history.html", entries=_store().list(), not_found=True), 404
    return render_template("report.html", result=doc)


@bp.route("/history/<analysis_id>/download.<fmt>")
def download_report(analysis_id, fmt):
    doc = _store().get(analysis_id)
    if doc is None:
        return render_template("history.html", entries=_store().list(), not_found=True), 404

    doc.pop("_id", None)
    stem = os.path.splitext(doc.get("filename") or "report")[0]

    if fmt == "json":
        body = json.dumps(doc, indent=2, default=str)
        return Response(
            body,
            mimetype="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}.json"'},
        )
    if fmt == "md":
        return Response(
            report_to_markdown(doc),
            mimetype="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{stem}.md"'},
        )
    return redirect(url_for("main.history_detail", analysis_id=analysis_id))


@bp.route("/view-uploads")
def view_uploads():
    return redirect(url_for("main.history"))


def _sample_names():
    try:
        return sorted(f for f in os.listdir(SAMPLES_DIR) if f.endswith(".code"))
    except OSError:
        return []


def _safe_sample_path(name):
    safe = secure_filename(name)
    path = os.path.join(SAMPLES_DIR, safe)
    if safe and safe.endswith(".code") and os.path.isfile(path):
        return path
    return None
