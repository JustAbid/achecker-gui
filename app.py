"""Flask web interface for the AChecker access control analysis tool."""

import os
import re
import sys
import subprocess
from datetime import datetime, timezone

from flask import Flask, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ACHECKER_SCRIPT = os.path.join(BASE_DIR, "bin", "achecker.py")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
ANALYSIS_TIMEOUT = int(os.environ.get("ACHECKER_TIMEOUT", "300"))  # seconds
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-not-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # don't let the browser cache css/js

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        files = list(_collection.find().sort("upload_time", -1))
    except PyMongoError:
        files = []
    return render_template("uploads.html", files=files, db_error=_db_unavailable())


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
                "upload_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    except PyMongoError:
        pass


def _db_unavailable():
    try:
        _mongo.admin.command("ping")
        return False
    except PyMongoError:
        return True


def _respond(result, status=200):
    # fetch() requests only need the results fragment, not the whole page
    template = "_results.html" if request.headers.get("X-Requested-With") == "fetch" else "index.html"
    return render_template(template, result=result), status


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(debug=debug)
