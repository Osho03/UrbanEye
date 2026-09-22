"""Real-time (SSE) event source for the UrbanEye admin panel.

One background watcher thread tails the MongoDB `issues` collection and feeds
a thread-safe queue. Two tailing strategies, chosen automatically:

* MongoDB **change streams** when the cluster supports them (Atlas / replica
  set) - zero polling, sub-second latency.
* A lightweight ``_id`` poll fallback every few seconds when running on a
  single-node local MongoDB, so the local/demo stack still gets a live feed.

SSE clients each render their own initial snapshot (recent issues), then
share the single watcher queue. Heartbeats are emitted by the HTTP generator,
not by this module.
"""

import logging
import queue
import threading
from datetime import datetime

try:
    import numpy as np
    _HAVE_NUMPY = True
except Exception:
    _HAVE_NUMPY = False

try:
    from config import issues_collection
except Exception:  # import safety (e.g. offline tests / absent DB)
    issues_collection = None

log = logging.getLogger("urbaneye.realtime")

QUEUE_MAX = 300
POLL_SECONDS = 2.0
SNAPSHOT_LIMIT = 30


def _clean(value):
    """Recursively convert a Mongo doc into JSON-safe native Python types."""
    from bson import ObjectId

    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if _HAVE_NUMPY and isinstance(value, np.generic):
        return value.item()
    return value


def _payload(doc, event, changed=None):
    data = _clean(doc)
    data["issue_id"] = str(data.get("_id") or "")
    photo = data.get("detected_image") or data.get("image_path")
    if photo:
        data["photo"] = str(photo).replace("\\", "/")
    data["event"] = event
    if changed:
        data["changed"] = changed
    return data


class _RealtimeFeed:
    def __init__(self):
        self._q = queue.Queue(maxsize=QUEUE_MAX)
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            t = threading.Thread(
                target=self._run, name="urbaneye-realtime", daemon=True
            )
            self._thread = t
            t.start()

    def snapshot(self, limit=SNAPSHOT_LIMIT):
        """Most recent issues, oldest-first, for a freshly-opened SSE client."""
        if issues_collection is None:
            return []
        try:
            docs = list(
                issues_collection.find({}).sort("_id", -1).limit(limit)
            )
        except Exception as e:
            log.warning("realtime snapshot failed: %s", e)
            return []
        return [_payload(d, "insert") for d in reversed(docs)]

    def next(self, timeout=12.0):
        """Blocking read of the next live event; None when the timeout elapses."""
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    # -- internal --------------------------------------------------------------

    def _put(self, item):
        try:
            self._q.put_nowait(item)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(item)
            except queue.Empty:
                pass

    def _run(self):
        if issues_collection is None:
            log.warning("realtime watcher idle: no database configured")
            return
        try:
            self._tail_change_stream()
            return
        except Exception as e:
            log.warning("change stream unavailable (%s) - using _id polling", e)
        self._tail_by_id()

    def _tail_change_stream(self):
        pipeline = [
            {"$match": {"operationType": {"$in": ["insert", "update"]}}}
        ]
        with issues_collection.watch(pipeline, full_document="update_lookup") as cursor:
            for change in cursor:
                op = change.get("operationType")
                if op not in ("insert", "update"):
                    continue
                doc = change.get("fullDocument")
                if not doc:
                    continue
                changed = None
                if op == "update":
                    keys = (change.get("updateDescription") or {}).get(
                        "updatedFields"
                    ) or {}
                    changed = {"fields": list(keys.keys())}
                self._put(_payload(doc, op, changed))

    def _tail_by_id(self):
        last_id = None
        while True:
            try:
                if last_id is None:
                    newest = issues_collection.find_one(
                        {}, {"_id": 1}, sort=[("_id", -1)]
                    )
                    last_id = newest["_id"] if newest else None
                    continue
                docs = list(
                    issues_collection.find({"_id": {"$gt": last_id}})
                    .sort("_id", 1)
                    .limit(100)
                )
                for d in docs:
                    oid = d.get("_id")
                    if oid is None:
                        continue
                    self._put(_payload(d, "insert"))
                    last_id = oid
            except Exception as e:
                log.warning("realtime polling error: %s", e)
            threading.Event().wait(POLL_SECONDS)


_feed = None
_feed_lock = threading.Lock()


def get_feed():
    """Lazy singleton: one shared watcher for every SSE client."""
    global _feed
    with _feed_lock:
        if _feed is None:
            _feed = _RealtimeFeed()
        _feed.start()
    return _feed