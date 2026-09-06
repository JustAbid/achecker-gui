"""MongoDB-backed analysis history.

Every method degrades gracefully when MongoDB is unreachable: writes become
no-ops and reads return ``None`` (which the views render as "history
unavailable"), so the analysis feature keeps working without a database.
"""

from datetime import datetime

import pytz
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_RAW_OUTPUT_CAP = 20_000  # characters


class HistoryStore:
    def __init__(self, uri, db_name, tz="Europe/Berlin", *, collection=None):
        if collection is not None:
            self._collection = collection
            self._client = None
        else:
            self._client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self._collection = self._client[db_name]["uploaded_files"]
        self._tz = pytz.timezone(tz)

    def available(self) -> bool:
        try:
            self._collection.database.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def save(self, filename, report):
        doc = {
            "filename": filename,
            "upload_time": datetime.now(self._tz).strftime("%Y-%m-%d %I:%M:%S %p"),
            **report.to_dict(),
            "raw_output": (report.raw_output or "")[:_RAW_OUTPUT_CAP],
        }
        try:
            return str(self._collection.insert_one(doc).inserted_id)
        except PyMongoError:
            return None

    def list(self, limit=200):
        try:
            return list(self._collection.find().sort("_id", -1).limit(limit))
        except PyMongoError:
            return None

    def get(self, analysis_id):
        try:
            return self._collection.find_one({"_id": ObjectId(analysis_id)})
        except (PyMongoError, InvalidId, TypeError):
            return None
