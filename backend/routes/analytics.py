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
    Predictive Maintenance: Find clusters of issues.
    """
    # Get all active issues (ignore resolved)
    issues = list(issues_collection.find(
        {"status": {"$in": ["Pending", "Assigned", "In Progress"]}},
        {"latitude": 1, "longitude": 1, "issue_type": 1}
    ))
    
    # Convert latitude/longitude to float if stored as strings
    for issue in issues:
        try:
            issue["latitude"] = float(issue["latitude"])
            issue["longitude"] = float(issue["longitude"])
        except:
            continue
            
    from ai.predictive_analytics import detect_hotspots
    # Find clusters within 50 meters, min 3 issues
    hotspots = detect_hotspots(issues, radius=50, min_count=3)
    
    return jsonify(hotspots)
