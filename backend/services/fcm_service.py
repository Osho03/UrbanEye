"""Firebase Cloud Messaging (FCM) integration for UrbanEye.

The backend pushes a message to the reporting citizen's device(s) whenever an
admin changes a report's status (Pending -> In Progress -> Resolved).

Requires a Firebase service account key:
  - On Render: set the env var FIREBASE_SERVICE_ACCOUNT_JSON to the full JSON
    string of the service account private key
    (Firebase console -> Project settings -> Service accounts -> Generate key).
  - Locally: alternatively set GOOGLE_APPLICATION_CREDENTIALS to a file path.

Everything degrades gracefully - if Firebase is not configured, no exception
escapes, the status update simply succeeds without push.
"""
import os
import tempfile
from typing import List, Optional

_firebase_app = None


def _get_app():
    """Lazily initialise the Firebase Admin app from env credentials."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

    tmp_path = None
    try:
        from firebase_admin import credentials, initialize_app

        if cred_json:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            )
            tmp.write(cred_json)
            tmp.close()
            tmp_path = tmp.name
            cert = credentials.Certificate(tmp_path)
        elif cred_path and os.path.exists(cred_path):
            cert = credentials.Certificate(cred_path)
        else:
            _firebase_app = None
            return _firebase_app

        _firebase_app = initialize_app(cert, name="urbaneye-fcm")
    except Exception as e:
        print(f"[fcm] Firebase not configured ({type(e).__name__}): {e}")
        _firebase_app = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return _firebase_app


def is_configured() -> bool:
    return _get_app() is not None


def send_status_update(
    tokens: List[str],
    *,
    issue_title: str,
    status: str,
    admin_remarks: str,
    issue_id: str,
    changed_at: str,
) -> int:
    """Push a status update to a citizen's devices. Returns sent count."""
    app = _get_app()
    if app is None:
        return 0
    tokens = [t for t in tokens if isinstance(t, str) and t.strip()]
    if not tokens:
        return 0

    try:
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title="UrbanEye · Status Update",
                body=f'"{issue_title}" is now {status}.'
                + (f" {admin_remarks}" if admin_remarks else ""),
            ),
            data={
                "type": "status_update",
                "issue_id": str(issue_id),
                "issue_title": issue_title,
                "status": str(status),
                "comment": admin_remarks or "",
                "changed_at": changed_at,
            },
            tokens=tokens[:5],
        )
        resp = messaging.send_multicast(message, app=app)
        print(f"[fcm] status update pushed: {resp.success_count} delivered")
        return int(resp.success_count or 0)
    except Exception as e:
        print(f"[fcm] send failed ({type(e).__name__}): {e}")
        return 0