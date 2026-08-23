import os
import threading
import time

from pymongo import MongoClient
from dotenv import load_dotenv

# Optional local .env loading (ignored on Render if file doesn't exist)
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Use Cloud URI if available, otherwise fallback to local
# Render will provide MONGO_URI directly in the environment
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# When MONGO_URI is explicitly configured we are in production:
# localhost is NOT an acceptable fallback target.
EXPLICIT_CLOUD = bool(os.getenv("MONGO_URI"))

CONNECT_TIMEOUT_MS = 20000


def _mask(uri):
    """Hide password in logs."""
    import re
    return re.sub(r"(//[^:/@]+):[^@]*@", r"\1:***@", uri)


def _try_connect(timeout_ms):
    c = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=CONNECT_TIMEOUT_MS,
    )
    c.admin.command("ping")  # force real handshake now, not lazily later
    return c


class _LazyClient:
    """Builds the real MongoClient on first use.

    A mongodb+srv:// URI whose cluster hostname does not resolve makes
    MongoClient(...) raise at construction time. Deferring that keeps
    gunicorn alive: the app deploys and serves /api/health, requests
    surface the error, and it recovers automatically once MONGO_URI or
    DNS is fixed.
    """

    def __init__(self, factory):
        self._factory = factory
        self._lock = threading.Lock()
        self._real = None

    def _resolve(self):
        if self._real is None:
            with self._lock:
                if self._real is None:
                    self._real = self._factory()
        return self._real

    def __getattr__(self, name):
        return getattr(self._resolve(), name)


class _LazyCollection:
    def __init__(self, lazy_db, name):
        self._lazy_db = lazy_db
        self._name = name

    def _coll(self):
        return self._lazy_db._db()[self._name]

    def __getattr__(self, name):
        return getattr(self._coll(), name)

    def __getitem__(self, key):
        return self._coll()[key]


class _LazyDatabase:
    def __init__(self, client_ref, name):
        self._client_ref = client_ref
        self._name = name

    def _db(self):
        c = self._client_ref
        real = c._resolve() if isinstance(c, _LazyClient) else c
        return real[self._name]

    def __getitem__(self, collection_name):
        return _LazyCollection(self, collection_name)

    def __getattr__(self, name):
        return getattr(self._db(), name)


client = None
attempts = 3 if EXPLICIT_CLOUD else 1
last_error = None

for attempt in range(1, attempts + 1):
    try:
        client = _try_connect(timeout_ms=15000)
        print(f"[db] Connected to MongoDB: {_mask(MONGO_URI)} "
              f"(attempt {attempt})")
        break
    except Exception as e:
        last_error = e
        print(f"[db] Attempt {attempt}/{attempts} failed for "
              f"{_mask(MONGO_URI)}: {type(e).__name__}: {e}")
        if attempt < attempts:
            time.sleep(4)

if client is None:
    if EXPLICIT_CLOUD:
        # Production: NEVER downgrade to localhost. Keep a lazy client pointed
        # at the configured cluster; individual requests will surface errors
        # until connectivity recovers (e.g. Atlas URI/IP whitelist fix).
        txt = str(last_error)
        hint = ""
        if ("DNS query name does not exist" in txt or "NXDOMAIN" in txt.upper()
                or "dnspython" in txt.lower()):
            hint = (" [SRV/DNS lookup failed: the Atlas hostname inside "
                    "MONGO_URI does not exist. Re-copy the connection string "
                    "from Atlas > Connect > Drivers and update MONGO_URI in "
                    "the Render dashboard.]")
        elif "whitelist" in txt.lower() or "timeout" in txt.lower():
            hint = (" [Check the Atlas Network Access IP whitelist includes "
                    "0.0.0.0/0 for Render, and that credentials are correct.]")
        print(f"[db] FATAL: MONGO_URI is configured but unreachable after "
              f"{attempts} attempts - keeping cloud client with NO localhost "
              f"fallback. Last error: {last_error}{hint}")
        client = _LazyClient(lambda: MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=CONNECT_TIMEOUT_MS,
        ))
    else:
        print("[db] No MONGO_URI configured - using local development DB")
        client = MongoClient("mongodb://localhost:27017",
                             serverSelectionTimeoutMS=5000)

db = _LazyDatabase(client, "urbaneye")
issues_collection = db["issues"]
