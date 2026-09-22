from flask import Blueprint, jsonify, request, send_from_directory, Response, stream_with_context

from config import issues_collection

import json
import os

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/stats", methods=["GET"])
def get_statistics():
    try:
        total = issues_collection.count_documents({})
        pending = issues_collection.count_documents({"status": "Pending"})
        assigned = issues_collection.count_documents({"status": "Assigned"})
        resolved = issues_collection.count_documents({"status": "Resolved"})
        
        # Phase 12: Handle mixed data types (old string, new object format)
        # Get all issues and extract issue_type manually
        all_issues = list(issues_collection.find({}, {"issue_type": 1, "assigned_department": 1, "severity_label": 1}))
        
        # Extract issue types (handle both string and object)
        type_counts = {}
        dept_counts = {}
        severity_counts = {}
        
        for issue in all_issues:
            # Handle issue_type (string OR object)
            issue_type = issue.get("issue_type")
            if isinstance(issue_type, dict):
                # Phase 12 object format
                type_str = issue_type.get("detected_type") or issue_type.get("primary_guess") or "Unknown"
            elif isinstance(issue_type, str):
                type_str = issue_type
            else:
                type_str = "Unknown"
            
            type_counts[type_str] = type_counts.get(type_str, 0) + 1
            
            # Handle department
            dept = issue.get("assigned_department") or "Unassigned"
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            # Handle severity
            severity = issue.get("severity_label") or "Normal"
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return jsonify({
            "total": total,
            "pending": pending,
            "assigned": assigned,
            "resolved": resolved,
            "autonomous": issues_collection.count_documents({"autonomous_action": "Processed"}),
            "by_type": type_counts,
            "by_dept": dept_counts,
            "by_severity": severity_counts
        })
    
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        # Return safe defaults instead of crashing
        return jsonify({
            "total": 0,
            "pending": 0,
            "assigned": 0,
            "resolved": 0,
            "by_type": {},
            "by_dept": {},
            "by_severity": {}
        })

@analytics_bp.route("/hotspots", methods=["GET"])
def get_hotspots():
    """
    Predictive Maintenance (Phase 4): DBSCAN density clustering.
    Finds hotspots of any shape; lonely issues are ignored as noise.
    """
    # Get all active issues (ignore resolved)
    issues = list(issues_collection.find(
        {"status": {"$in": ["Pending", "Assigned", "In Progress"]}},
        {"latitude": 1, "longitude": 1, "issue_type": 1,
         "severity_label": 1}
    ))

    try:
        from ai.hotspot_engine import detect_hotspots
        hotspots = detect_hotspots(issues, radius=50, min_count=3)
    except Exception as e:
        print(f"DBSCAN engine failed ({e}) - legacy fallback")
        from ai.predictive_analytics import detect_hotspots as legacy
        for issue in issues:
            try:
                issue["latitude"] = float(issue["latitude"])
                issue["longitude"] = float(issue["longitude"])
            except Exception:
                continue
        hotspots = legacy(issues, radius=50, min_count=3)

    return jsonify(hotspots)


@analytics_bp.route("/patterns", methods=["GET"])
def get_patterns():
    """
    Phase 4: Seasonal pattern mining over the last 12 months of history.
    Returns monthly matrices per issue type, monsoon-style spikes,
    weekday load profile and plain-language recommendations.
    """
    from datetime import datetime, timedelta
    try:
        from ai.seasonal_mining import mine_patterns
    except ImportError as e:
        print(f"seasonal_mining unavailable: {e}")
        return jsonify({"status": "unavailable", "message": "Pattern mining needs pandas on the server."})

    year_ago = datetime.now() - timedelta(days=365)
    issues = list(issues_collection.find(
        {"created_at": {"$gte": year_ago}},
        {"issue_type": 1, "created_at": 1}
    ))
    return jsonify(mine_patterns(issues))


@analytics_bp.route("/priority-model", methods=["GET"])
def priority_model_status():
    """Phase 4: is the self-training priority brain active yet?"""
    try:
        from ai.priority_model import model_status
    except ImportError as e:
        print(f"priority_model unavailable: {e}")
        return jsonify({"active": False, "reason": "Priority model needs scikit-learn/joblib on the server."})
    return jsonify(model_status())


# ---------------------------------------------------------------------------
# Model Evaluation & Benchmark Suite
# Runs every deployed vision model against the labelled dataset and (optionally)
# retrains a classifier with a proper stratified holdout. Produces honest
# P/R/F1 + confusion-matrix artifacts for review/demo.
# ---------------------------------------------------------------------------
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "ai", "evaluation")


@analytics_bp.route("/model-evaluation", methods=["GET"])
def model_evaluation():
    try:
        from ai.evaluator import (latest_report, run_evaluation,
                                  train_and_evaluate_classifier)
    except ImportError as e:
        return jsonify({"status": "unavailable", "message": f"evaluator missing: {e}"})

    do_refresh = request.args.get("refresh", "").lower() in ("1", "true", "yes")
    do_train = request.args.get("train", "").lower() in ("1", "true", "yes")
    if do_train:
        try:
            train_and_evaluate_classifier()
        except Exception as e:
            print(f"model-evaluation train failed: {e}")
            return jsonify({"status": "error", "message": str(e)})
    if do_refresh:
        try:
            run_evaluation()
        except Exception as e:
            print(f"model-evaluation refresh failed: {e}")
            return jsonify({"status": "error", "message": str(e)})

    base = request.base_url
    payload = {"status": "ok", "chart_base": base}
    report = latest_report()
    if report:
        payload["deployed_models"] = report.get("models")
        payload["eval_set"] = {
            "n_samples": report.get("n_samples"),
            "classes": report.get("class_order"),
            "generated_at": report.get("generated_at"),
            "note": ("Out-of-distribution stress test on web-scraped images - "
                     "expected to be much harder than in-domain citizen photos"),
        }
        for model_name, m in (report.get("models") or {}).items():
            charts = m.get("charts") or {}
            for key, fn in charts.items():
                payload.setdefault("charts", {})[f"{model_name}/{key}"] = \
                    f"{base}/{fn}"
    else:
        payload["models"] = {}
        payload["eval_set"] = {"note": "no report yet - call with ?refresh=1"}

    holdout = _latest_holdout()
    if holdout:
        payload["holdout_study"] = {
            "method": holdout.get("method"),
            "metrics": holdout.get("metrics"),
            "generated_at": holdout.get("generated_at"),
        }
        for key, fn in (holdout.get("charts") or {}).items():
            payload.setdefault("charts", {})[f"holdout/{key}"] = f"{base}/{fn}"
    return jsonify(payload)


def _latest_holdout():
    import glob
    import json as _json
    if not os.path.isdir(EVAL_DIR):
        return None
    files = glob.glob(os.path.join(EVAL_DIR, "holdout_*.json"))
    if not files:
        return None
    path = max(files, key=os.path.getmtime)
    try:
        with open(path) as f:
            return _json.load(f)
    except Exception:
        return None


@analytics_bp.route("/model-evaluation/<path:filename>", methods=["GET"])
def model_evaluation_artifact(filename):
    """Serve a generated report chart (confusion matrix / performance PNG)."""
    safe = os.path.basename(filename)
    if not os.path.isdir(EVAL_DIR):
        return jsonify({"status": "error", "message": "no evaluation dir"}), 404
    return send_from_directory(EVAL_DIR, safe)


@analytics_bp.route("/benchmark", methods=["POST"])
def benchmark():
    """
    'Run benchmark now' - re-measure every model against the held-out set in
    a background thread and return immediately. Poll /model-health until
    benchmark.running is false.
    """
    try:
        from ai.evaluator import start_benchmark_async
        result = start_benchmark_async()
        return jsonify(result), 202 if result["status"] == "started" else 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/model-health", methods=["GET"])
def model_health():
    """
    AI Model Health: retraining status + latest evaluation metrics + charts.
    Backs the 'AI Model Health' card in the app home screen.
    Optional query params:
      ?refresh=1  -> re-run the evaluation benchmark now
      ?train=1    -> force a full retrain now (then re-evaluate)
    """
    try:
        from ai.auto_retrain import model_health, maybe_auto_retrain
    except ImportError as e:
        return jsonify({"status": "unavailable", "message": f"{e}"})

    if request.args.get("train", "").lower() in ("1", "true", "yes"):
        result = maybe_auto_retrain(issues_collection, force=True,
                                    evaluate=True)
        return jsonify({"retrain": result, **model_health()})
    if request.args.get("refresh", "").lower() in ("1", "true", "yes"):
        try:
            from ai.evaluator import run_evaluation
            run_evaluation()
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    payload = model_health()

    # async benchmark job status for the app "Run benchmark now" button
    try:
        from ai.evaluator import benchmark_status
        payload["benchmark"] = benchmark_status()
    except Exception:
        pass

    # attach chart urls from the latest report
    try:
        from ai.evaluator import latest_report
        report = latest_report()
        base = request.base_url.replace("/model-health", "/model-evaluation")
        if report:
            charts = {}
            for model_name, m in (report.get("models") or {}).items():
                for key, fn in (m.get("charts") or {}).items():
                    charts[f"{model_name}/{key}"] = f"{base}/{fn}"
            payload["charts"] = charts
    except Exception:
        pass
    return jsonify(payload)


# ---------------------------------------------------------------------------
# Phase 16: Real-time time-series & anomaly endpoints for the live dashboard
# ---------------------------------------------------------------------------

@analytics_bp.route("/trends", methods=["GET"])
def get_trends():
    """
    Time-series of reported issues grouped by day or hour across N days.
    Query params: ?days=30 (default) & ?granularity=daily|hourly (default daily)
    """
    days = request.args.get("days", default=30, type=int)
    granularity = request.args.get("granularity", default="daily")
    days = max(1, min(days, 365))
    try:
        from ai.time_series_analytics import build_trends
        docs = list(issues_collection.find(
            {}, {"created_at": 1, "issue_type": 1}))
        return jsonify(build_trends(docs, days=days, granularity=granularity))
    except Exception as e:
        print(f"❌ Trends error: {e}")
        return jsonify({"status": "error", "message": str(e)})


@analytics_bp.route("/anomalies", methods=["GET"])
def get_anomalies():
    """
    Real-time anomaly detection: flags issue-types whose report rate in the
    last 24h deviates from the 7-day baseline (Poisson-normal z-score).
    """
    try:
        from ai.time_series_analytics import detect_anomalies
        docs = list(issues_collection.find(
            {}, {"created_at": 1, "issue_type": 1}))
        return jsonify(detect_anomalies(docs))
    except Exception as e:
        print(f"❌ Anomaly detection error: {e}")
        return jsonify({"status": "error", "message": str(e)})


@analytics_bp.route("/stream", methods=["GET"])
def realtime_stream():
    """
    Server-Sent Events. Pushes every new/updated issue to connected
    dashboards. Emits an initial 'snapshot' batch (recent issues) followed
    by live events; '-: keep-alive' comments keep the socket warm for
    gunicorn's response timeout.
    """
    try:
        from services.realtime import get_feed
    except Exception as e:
        print(f"❌ realtime feed unavailable: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    feed = get_feed()

    def generate():
        for payload in feed.snapshot():
            yield f"event: snapshot\ndata: {json.dumps(payload)}\n\n"
        while True:
            payload = feed.next(timeout=12)
            if payload is None:
                yield ": keep-alive\n\n"
                continue
            event_name = "update" if payload.get("event") == "update" \
                else "message"
            yield f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
