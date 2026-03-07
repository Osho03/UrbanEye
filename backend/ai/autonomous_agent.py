"""
UrbanEye AI - Autonomous Agent
This script acts as an autonomous worker that processes pending civic complaints.
It mimics an n8n workflow by automatically:
1. Fetching pending issues.
2. Analyzing them with the AI Inspector.
3. Automatically assigning departments and priorities.
4. Marking them as "Processed by AI".
"""

import time
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Add backend to path to import AI modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

try:
    from ai.inspector_agent import generate_inspection_summary
except ImportError:
    print("⚠️  AI Inspector module not found. Please ensure it's in backend/ai/inspector_agent.py")
    sys.exit(1)

# Database connection
try:
    from config import issues_collection, db
except ImportError:
    # Fallback for direct script execution if config not found
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    db = client["urbaneye"]
    issues_collection = db["issues"]

# Department mapping
DEPARTMENT_MAPPING = {
    "pothole": "Road Department",
    "garbage": "Sanitation Department",
    "water_leak": "Water Board",
    "streetlight": "Electricity Department"
}

def process_pending_issues():
    """Fetches and processes all pending issues autonomously"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Autonomous Agent waking up...")
    
    # Find issues with status 'Pending' or missing status
    pending_issues = list(issues_collection.find({
        "$or": [
            {"status": "Pending"},
            {"status": {"$exists": False}},
            {"autonomous_status": "Queued"}
        ],
        "autonomous_action": {"$ne": "Processed"} # Don't re-process
    }))
    
    if not pending_issues:
        print("   No pending issues found. Sleeping... 😴")
        return 0
        
    print(f"   Found {len(pending_issues)} pending issues to process.")
    
    count = 0
    for issue in pending_issues:
        issue_id = str(issue["_id"])
        title = issue.get("title", "Untitled")
        print(f"   👉 Processing: {title} ({issue_id})")
        
        # 1. Run AI Inspection
        analysis = generate_inspection_summary(issue)
        
        # 2. Determine automation logic (The 'n8n' part)
        priority_score = analysis.get("priority_score", 0)
        issue_type = issue.get("issue_type", "unknown")
        
        # Hard automation rules
        new_status = "Assigned"
        assigned_dept = DEPARTMENT_MAPPING.get(issue_type, "General Maintenance")
        
        priority_label = "Low"
        if priority_score >= 80: priority_label = "High"
        elif priority_score >= 40: priority_label = "Medium"
        
        # 3. Update Database
        update_data = {
            "status": new_status,
            "assigned_department": assigned_dept,
            "priority": priority_label.lower(),
            "ai_priority_score": priority_score,
            "autonomous_action": "Processed",
            "autonomous_timestamp": datetime.now(),
            "admin_remarks": f"🤖 AUTO-ACTION: {analysis.get('suggested_action')}. Decision based on {', '.join(analysis.get('explanations', []))}",
            "last_processed_by": "Autonomous AI Agent"
        }
        
        issues_collection.update_one(
            {"_id": issue["_id"]},
            {"$set": update_data}
        )
        
        print(f"      ✅ AUTO-ASSIGNED to {assigned_dept} (Priority: {priority_label})")
        count += 1
        
    return count

if __name__ == "__main__":
    print("🚀 UrbanEye Autonomous Agent Started")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            processed = process_pending_issues()
            if processed > 0:
                print(f"   Success! Processed {processed} issues.")
            
            # Run every 30 seconds (for demo purposes)
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Autonomous Agent stopped.")
