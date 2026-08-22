from flask import Blueprint, jsonify
from pymongo import MongoClient

analytics_bp = Blueprint("analytics", __name__)

# Database connection
client = MongoClient("mongodb://localhost:27017/")
db = client["urbaneye"]
issues_collection = db["issues"]

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
