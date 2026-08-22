import os
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
        # Production: NEVER downgrade to localhost. Keep a live client pointed
        # at the configured cluster; individual requests will surface errors
        # until connectivity recovers (e.g. Atlas IP whitelist fix).
        print(f"[db] FATAL: MONGO_URI is configured but unreachable "
              f"after {attempts} attempts. Keeping cloud client - NO "
              f"localhost fallback. Last error: {last_error}")
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=CONNECT_TIMEOUT_MS,
        )
    else:
        print("[db] No MONGO_URI configured - using local development DB")
        client = MongoClient("mongodb://localhost:27017",
                             serverSelectionTimeoutMS=5000)

db = client["urbaneye"]
issues_collection = db["issues"]
