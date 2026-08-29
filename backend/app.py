from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

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


@app.route("/api/health/yolo")
def health_yolo():
    """Temporary diagnostics: run the exact YOLO image path used by report."""
    import traceback
    info = {}
    for name in ("yolo_detector", "yolo_onnx", "annotate",
                 "metadata_forensics", "duplicate_detector"):
        try:
            __import__(f"ai.{name}", fromlist=["*"])
            info[name] = "ok"
        except Exception as e:
            info[name] = f"IMPORT FAIL: {type(e).__name__}: {e}"
    try:
        import cv2
        info["cv2"] = cv2.__version__
        import numpy as np
        import onnxruntime
        info["onnxruntime"] = onnxruntime.__version__
    except Exception as e:
        info["libs"] = f"{type(e).__name__}: {e}"

    import os
    info["onnx_exists"] = os.path.isabs("a") or os.path.exists(
        os.path.join("ai", "models", "civic_yolov8.onnx"))
    info["pt_exists"] = os.path.exists(
        os.path.join("ai", "models", "civic_yolov8.pt"))
    try:
        from ai.yolo_detector import detect_issue
        arr = (np.random.rand(320, 320, 3) * 255).astype("uint8")
        tmp = os.path.join(os.getcwd(), "_yolo_diag.png")
        cv2.imwrite(tmp, arr)
        info["detect_result"] = detect_issue(tmp)
        os.remove(tmp) if os.path.exists(tmp) else None
    except Exception as e:
        info["DETECT_FAIL"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    return info, 200


@app.route("/api/health/flow", methods=["POST"])
def health_flow():
    """Temp: trace each image-branch step of /api/issues/report on a real upload."""
    import os
    import traceback
    from flask import request
    out = {}
    img = request.files.get("image")
    if not img:
        return {"error": "no image"}, 400
    ext = os.path.splitext(img.filename)[1]
    if ext.lower() in ("", ".jfif"):
        ext = ".jpg"
    os.makedirs("uploads", exist_ok=True)
    p = os.path.join("uploads", "_flow_diag" + ext)
    img.save(p)

    try:
        from ai.duplicate_detector import compute_dhash, find_potential_duplicate
        h = compute_dhash(p)
        out["dhash"] = h
        dupe = find_potential_duplicate(h, 12.97, 77.59)
        out["duplicate"] = None if not dupe else dupe.get("_id")
    except Exception as e:
        out["dhash"] = f"FAIL {type(e).__name__}: {e}\n{traceback.format_exc()}"

    r = None
    try:
        from ai.yolo_detector import detect_issue
        r = detect_issue(p)
        out["detect"] = (r["issue_type"], r["confidence"], r["model_source"]) if r else None
    except Exception as e:
        out["detect"] = f"FAIL {type(e).__name__}: {e}\n{traceback.format_exc()}"

    try:
        from ai.annotate import annotate_detection
        out["annotate"] = annotate_detection(p, r) if r else "skip (no detect)"
    except Exception as e:
        out["annotate"] = f"FAIL {type(e).__name__}: {e}\n{traceback.format_exc()}"

    try:
        from ai.metadata_forensics import analyze_metadata
        out["forensics"] = analyze_metadata(p)
    except Exception as e:
        out["forensics"] = f"FAIL {type(e).__name__}: {e}\n{traceback.format_exc()}"

    try:
        from ai.impact_radius import calculate_impact_radius
        from routes.routing import get_routing_info
        sev = r["severity_score"] if r else "Low"
        out["impact"] = calculate_impact_radius(12.97, 77.59, sev)
        out["routing"] = get_routing_info(r["issue_type"] if r else "unknown")
    except Exception as e:
        out["post"] = f"FAIL {type(e).__name__}: {e}\n{traceback.format_exc()}"

    if p and os.path.exists(p):
        os.remove(p)
    return out, 200

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

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    clean_name = filename.replace("uploads/", "").replace("uploads\\", "")
    return send_from_directory("uploads", clean_name)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
