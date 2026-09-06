"""Flask web interface for the AChecker access control analysis tool."""

import os
import re
import sys
import subprocess
from datetime import datetime

import pytz
from flask import Flask, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ACHECKER_SCRIPT = os.path.join(BASE_DIR, "bin", "achecker.py")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
ANALYSIS_TIMEOUT = int(os.environ.get("ACHECKER_TIMEOUT", "300"))  # seconds
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
TZ = pytz.timezone(os.environ.get("ACHECKER_TZ", "Europe/Berlin"))

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-not-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.after_request
def no_store(response):
    # keep the browser from serving a stale page (e.g. old history after an analysis)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.context_processor
def asset_helpers():
    # append the file's mtime to static URLs so a changed css/js is never cached
    def static_url(filename):
        try:
            version = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
        except OSError:
            version = 0
        return url_for("static", filename=filename, v=version)

    return {"static_url": static_url}


# Mongo is optional. If it's down we just skip the history bit.
_mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
_collection = _mongo["achecker_db"]["uploaded_files"]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


@app.route("/")
def index():
    return render_template("index.html", result=None)


@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded = request.files.get("file")
    if uploaded is None or uploaded.filename == "":
        return _respond({"error": "No file selected."}, status=400)

    filename = secure_filename(uploaded.filename)
    if not filename:
        return _respond({"error": "Invalid file name."}, status=400)

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    uploaded.save(file_path)
    _record_upload(filename)

    return _respond(run_achecker(file_path))


@app.route("/view-uploads")
def view_uploads():
    try:
        # sort by _id: it's time-ordered, so this stays correct regardless of
        # how the upload_time string is formatted
        files = list(_collection.find().sort("_id", -1))
        db_error = False
    except PyMongoError:
        files, db_error = [], True
    return render_template("uploads.html", files=files, db_error=db_error)


def run_achecker(file_path):
    """Run AChecker on the file and return a dict for the template."""
    try:
        result = subprocess.run(
            [sys.executable, ACHECKER_SCRIPT, "-f", file_path, "-b"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=ANALYSIS_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Analysis timed out after {ANALYSIS_TIMEOUT} seconds."}
    except OSError as exc:
        return {"error": f"Could not start AChecker: {exc}"}

    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        return {"error": message or "AChecker exited with an error."}

    return {"sections": parse_report(result.stdout)}


def parse_report(output):
    """Split AChecker's stdout into sections of {title, blocks}."""
    output = ANSI_RE.sub("", output)
    sections = []
    for chunk in output.split("Checking contract for"):
        chunk = chunk.strip()
        if not chunk:
            continue
        title, _, rest = chunk.partition("------------------")
        blocks = [block.strip() for block in rest.split("------------------") if block.strip()]
        sections.append({"title": f"Checking contract for {title.strip()}", "blocks": blocks})
    return sections


def _record_upload(filename):
    try:
        _collection.insert_one(
            {
                "filename": filename,
                "upload_time": datetime.now(TZ).strftime("%Y-%m-%d %I:%M:%S %p"),
            }
        )
    except PyMongoError as exc:
        app.logger.warning("could not save upload history (is MongoDB running?): %s", exc)


def _respond(result, status=200):
    # fetch() requests only need the results fragment, not the whole page
    template = "_results.html" if request.headers.get("X-Requested-With") == "fetch" else "index.html"
    return render_template(template, result=result), status


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=debug)
