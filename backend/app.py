from flask import Flask, send_from_directory, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import mimetypes

from config import db as mongo_db

# Optional local .env loading
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None 
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    """Root route for Render's default health check"""
    return jsonify({"status": "live", "message": "UrbanEye API is online"}), 200

@app.route("/api/health")
def health_check():
    """Ultra-fast health check for Render"""
    return {"status": "ok", "message": "UrbanEye Live", "build": "phase4-dbcheck"}, 200


@app.route("/api/health/db")
def health_db():
    """Diagnose DB connectivity from inside the server. Never leaks credentials."""
    import re
    from config import client as db_client, MONGO_URI
    masked = re.sub(r"(//[^:/@]+):[^@]*@", r"\1:***@", MONGO_URI)
    try:
        db_client.admin.command("ping")
        n = None
        try:
            from config import issues_collection
            n = issues_collection.count_documents({})
        except Exception as e2:
            n = f"count failed: {type(e2).__name__}"
        return {"db": "reachable", "uri": masked, "issue_count": n}, 200
    except Exception as e:
        return {"db": "UNREACHABLE", "uri": masked,
                "error": f"{type(e).__name__}: {e}"}, 200


@app.errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

# Try/Except for Chatbot to prevent crash
try:
    from routes.chatbot import bp as chatbot_bp
    CHATBOT_AVAILABLE = True
except (ImportError, Exception):
    CHATBOT_AVAILABLE = False

# Lazy-load blueprints
from routes.issue import issue_bp
from routes.admin import admin_bp
from routes.analytics import analytics_bp
from routes.user import user_bp
from routes.features import features_bp

app.register_blueprint(issue_bp, url_prefix="/api/issues")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(user_bp, url_prefix="/api/user")
app.register_blueprint(features_bp, url_prefix="/api/features")

if CHATBOT_AVAILABLE:
    app.register_blueprint(chatbot_bp)

PLACEHOLDER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#667eea"/><stop offset="1" stop-color="#764ba2"/>'
    '</linearGradient></defs>'
    '<rect width="200" height="200" rx="18" fill="url(#g)" opacity="0.92"/>'
    '<g fill="none" stroke="#ffffff" stroke-width="5" stroke-linejoin="round" opacity="0.95">'
    '<rect x="56" y="54" width="88" height="72" rx="12"/>'
    '<circle cx="100" cy="90" r="18"/>'
    '<path d="M68 58 L76 42 L124 42 L132 58"/>'
    '</g>'
    '<text x="100" y="152" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" '
    'font-size="15" text-anchor="middle" opacity="0.92">Evidence not archived</text>'
    '</svg>'
)


def _placeholder_image():
    return Response(PLACEHOLDER_SVG, mimetype="image/svg+xml")


def _serve_upload(clean_name):
    """Serve an uploaded file. Tries the local disk first (fast path), then the
    durable MongoDB copy (survives Render's ephemeral disk being wiped on
    redeploy), and finally falls back to a built-in placeholder instead of a 404."""
    if not clean_name or clean_name.startswith((".", "/", "\\")):
        return _placeholder_image()

    local = os.path.join("uploads", clean_name)
    if os.path.isfile(local):
        return send_from_directory("uploads", clean_name)

    try:
        rec = mongo_db["uploaded_files"].find_one(
            {"filename": clean_name}, {"_id": 0, "data": 1, "mimetype": 1}
        )
        if rec and rec.get("data"):
            mime = rec.get("mimetype") or \
                mimetypes.guess_type(clean_name)[0] or "application/octet-stream"
            if mime.startswith("text/"):
                mime = "application/octet-stream"
            return Response(rec["data"], mimetype=mime)
    except Exception as e:
        print(f"[uploads] Mongo lookup failed for {clean_name}: {type(e).__name__}: {e}")

    return _placeholder_image()


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    clean_name = filename.replace("uploads/", "").replace("uploads\\", "")
    return _serve_upload(clean_name)

# Autonomous retraining scheduler (daemon thread). Surveys MongoDB every
# UR_SCHED_MINUTES; retrains when new verified images accumulate, then
# refreshes the evaluation report for Model Health. Optional on low-RAM hosts
# via UR_AUTO_RETRAIN=0.
try:
    from ai.auto_retrain import scheduler_start
    scheduler_start()
except Exception as e:
    print(f"[app] auto retrain scheduler unavailable: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
