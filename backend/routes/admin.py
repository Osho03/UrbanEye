from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
import os

# AI modules will be lazy-loaded inside routes to prevent startup timeouts
summarizer = None
voice_synth = None

admin_bp = Blueprint("admin", __name__)

# Database connection
from config import issues_collection, db
autonomous_logs = db["autonomous_logs"]


# Department mapping
DEPARTMENT_MAPPING = {
    "pothole": "Road Department",
    "garbage": "Sanitation Department",
    "water_leak": "Water Board",
    "streetlight": "Electricity Department"
}

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    # Simple auth for Phase 2A
    # TODO: Implement proper JWT in Phase 3
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if username == "osho" and password == "osho@2006":
        return jsonify({"success": True, "token": "admin-token", "user": {"username": "osho", "role": "admin"}})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@admin_bp.route("/issues", methods=["GET"])
def get_all_issues_admin():
    # Get all issues with full details
    try:
        issues = list(issues_collection.find({}))
        
        # Process issues
        for issue in issues:
            # Convert ObjectId to string for JSON serialization
            if "_id" in issue:
                issue["issue_id"] = str(issue["_id"])
                del issue["_id"]
                
            # Add auto-assigned department if not present
            if "assigned_department" not in issue:
                issue["assigned_department"] = DEPARTMENT_MAPPING.get(
                    issue.get("issue_type"), 
                    "Unassigned"
                )
        
        # Sort by timestamp (newest first)
        issues.reverse()
        
        return jsonify(issues)
    except Exception as e:
        print(f"❌ Admin issues error: {e}")
        return jsonify([]) # Return empty list on failure

@admin_bp.route("/issues/<issue_id>", methods=["GET"])
def get_issue_by_id(issue_id):
    try:
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return jsonify({"success": False, "message": "Issue not found"}), 404
        
        # Convert ObjectId to string
        issue["issue_id"] = str(issue["_id"])
        del issue["_id"]
        
        # Add auto-assigned department if not present
        if "assigned_department" not in issue:
            issue["assigned_department"] = DEPARTMENT_MAPPING.get(
                issue.get("issue_type"), 
                "Unassigned"
            )
            
        return jsonify(issue)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@admin_bp.route("/issues/<issue_id>/verify", methods=["POST"])
def verify_issue(issue_id):
    # Admin verifies/corrects AI output
    data = request.json
    corrected_type = data.get("corrected_type")
    is_valid = data.get("is_valid")
    
    try:
        # Update issue using ObjectId
        result = issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {
                "verified": True,
                "corrected_type": corrected_type,
                "is_valid": is_valid,
                "verified_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Issue not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@admin_bp.route("/issues/<issue_id>/assign", methods=["POST"])
def assign_department(issue_id):
    # Assign issue to department
    data = request.json
    department = data.get("department")
    priority = data.get("priority", "normal")
    
    try:
        issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {
                "assigned_department": department,
                "priority": priority,
                "status": "Assigned",
                "assigned_at": datetime.now()
            }}
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@admin_bp.route("/issues/<issue_id>/status", methods=["POST"])
def update_issue_status(issue_id):
    """Update issue status and optionally notify citizen"""
    data = request.json
    new_status = data.get("status")
    admin_remarks = data.get("admin_remarks", "")
    send_notification = data.get("send_notification", True)  # Default: send email
    
    try:
        # Get current issue state
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return jsonify({"success": False, "message": "Issue not found"}), 404
        
        old_status = issue.get("status", "Pending")
        
        # Phase 9: Update with status history
        update_data = {
            "$set": {
                "status": new_status,
                "admin_remarks": admin_remarks,
                "updated_at": datetime.now()
            },
            "$push": {
                "status_history": {
                    "old_status": old_status,
                    "new_status": new_status,
                    "changed_at": datetime.now(),
                    "changed_by": "Admin",
                    "comment": admin_remarks
                }
            }
        }
        
        result = issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            update_data
        )
        
        # Phase 9: Send notification if requested and email available
        if send_notification and result.modified_count > 0:
            reporter_email = issue.get("reporter_email")
            notify_enabled = issue.get("notify_on_updates", True)
            
            if reporter_email and notify_enabled:
                try:
                    from services.notification_service import notification_service
                    notification_type = "resolved" if new_status == "Resolved" else "status_update"
                    
                    notification_data = {
                        "issue_id": issue_id,
                        "issue_type": issue.get("issue_type", "Issue"),
                        "address": issue.get("address", "Unknown location"),
                        "status": new_status,
                        "admin_remarks": admin_remarks
                    }
                    
                    email_sent = notification_service.send_notification(
                        reporter_email,
                        notification_type,
                        notification_data
                    )
                    
                    # Log notification
                    if email_sent:
                        issues_collection.update_one(
                            {"_id": ObjectId(issue_id)},
                            {"$push": {
                                "notification_history": {
                                    "type": notification_type,
                                    "sent_at": datetime.now(),
                                    "status": "sent"
                                }
                            }}
                        )
                except Exception as e:
                    print(f"Notification error (non-critical): {e}")
        
        if result.modified_count > 0:
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "No changes made"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

# ==================== PHASE 10: AI AUTO-RESOLUTION ENGINE ====================
# Advisory AI recommendations (read-only, non-executing)

@admin_bp.route("/issues/<issue_id>/ai-recommendation", methods=["GET"])
def get_ai_recommendation(issue_id):
    """
    Get AI-powered recommendation for an issue
    IMPORTANT: This is ADVISORY ONLY - does not auto-execute any actions
    """
    try:
        # Fetch issue from database
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        
        if not issue:
            return jsonify({"success": False, "message": "Issue not found"}), 404
        
        # Import AI modules
        from ai.auto_resolution_engine import analyze_issue, recommend_contractor
        from data.contractors import get_all_contractors
        
        # Get AI recommendation
        ai_recommendation = analyze_issue(issue)
        
        # Get contractor recommendations
        contractors = get_all_contractors()
        contractor_recommendations = recommend_contractor(issue, contractors)
        
        # Combine results
        response = {
            "success": True,
            "disclaimer": "AI recommendations are advisory only. Final decisions rest with administrators.",
            "issue_id": issue_id,
            "issue_type": issue.get("issue_type", "unknown"),
            "current_status": issue.get("status", "Pending"),
            "ai_analysis": {
                "suggested_priority": ai_recommendation["suggested_priority"],
                "priority_score": ai_recommendation["priority_score"],
                "suggested_action": ai_recommendation["suggested_action"],
                "confidence_score": ai_recommendation["confidence_score"],
                "urgency_class": ai_recommendation["urgency_class"],
                "reasoning": ai_recommendation["reasoning"],
                "score_breakdown": ai_recommendation["factors"]
            },
            "contractor_recommendations": contractor_recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ AI Recommendation Error: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== PHASE 13: SUMMARIZATION & VOICE ENDPOINTS ====================

@admin_bp.route("/issues/<issue_id>/summary/generate", methods=['POST'])
def generate_summary(issue_id):
    """Generate AI summary for an issue"""
    global summarizer
    if not summarizer:
        try:
            from ai.summarizer import summarizer as ai_summarizer
            summarizer = ai_summarizer
        except ImportError:
            return jsonify({"error": "Summarizer module not found"}), 503
            
    if not summarizer:
        return jsonify({"error": "Summarizer not available. Please configure OpenAI API key."}), 503
    
    try:
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return jsonify({"error": "Issue not found"}), 404
        
        description = issue.get('description', '')
        if not description or len(description) < 20:
            return jsonify({"error": "Description too short to summarize"}), 400
        
        # Generate summary
        summary = summarizer.summarize(
            description,
            issue_type=issue.get('issue_type'),
            location=issue.get('location'),
            severity=issue.get('severity_label')
        )
        
        # Extract key points
        key_points = summarizer.extract_key_points(description)
        
        # Update database
        issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {"summary": summary, "key_points": key_points, "summary_generated_at": datetime.now()}}
        )
        
        return jsonify({"success": True, "summary": summary, "key_points": key_points})
        
    except Exception as e:
        print(f"❌ Summary generation error: {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/issues/<issue_id>/voice/generate", methods=['POST'])
def generate_voice(issue_id):
    """Generate voice audio for issue summary"""
    global voice_synth, summarizer
    if not voice_synth:
        try:
            from ai.text_to_speech import voice_synth as ai_voice
            voice_synth = ai_voice
        except ImportError:
            return jsonify({"error": "Voice module not found"}), 503

    if not voice_synth:
        return jsonify({"error": "Voice synthesis module not loaded. Check server logs."}), 503
    
    try:
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return jsonify({"error": "Issue not found"}), 404
        
        # Get or generate summary
        summary = issue.get('summary')
        if not summary:
            if not summarizer:
                return jsonify({"error": "No summary available"}), 400
            summary = summarizer.summarize(issue.get('description', ''), issue_type=issue.get('issue_type'))
            issues_collection.update_one({"_id": ObjectId(issue_id)}, {"$set": {"summary": summary}})
        
        # Generate audio
        voice = request.json.get('voice', 'alloy') if request.json else 'alloy'
        audio_path = voice_synth.generate_speech(summary, issue_id=issue_id, voice=voice)
        
        if not audio_path:
            return jsonify({"error": "Failed to generate audio"}), 500
        
        # Update database
        issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$set": {"audio_path": audio_path, "audio_voice": voice, "audio_generated_at": datetime.now()}}
        )
        
        return jsonify({"success": True, "audio_url": f"/api/admin/audio/{os.path.basename(audio_path)}"})
        
    except Exception as e:
        print(f"❌ Voice generation error: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== PHASE 15: AUTONOMOUS AGENT CONTROL ====================

@admin_bp.route("/autonomous/trigger", methods=["POST"])
def trigger_autonomous_agent():
    """Trigger the autonomous agent to process pending issues"""
    try:
        import subprocess
        import sys
        
        # Path to autonomous_agent.py
        agent_path = os.path.join(os.path.dirname(__file__), "..", "ai", "autonomous_agent.py")
        
        # Run as a one-shot process (not the loop)
        # We'll pass a flag to tell it to run once and exit
        python_exe = sys.executable or "python"
        
        # We'll actually just import and call the function for better control
        from ai.autonomous_agent import process_pending_issues
        count = process_pending_issues()
        
        # Log the action
        autonomous_logs.insert_one({
            "action": "Manual Trigger",
            "timestamp": datetime.now(),
            "issues_processed": count,
            "triggered_by": "Admin"
        })
        
        return jsonify({
            "success": True, 
            "message": f"Autonomous agent processed {count} issues.",
            "count": count
        })
    except Exception as e:
        print(f"❌ Autonomous trigger error: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/autonomous/status", methods=["GET"])
def get_autonomous_status():
    """Get status and history of autonomous agent"""
    try:
        logs = list(autonomous_logs.find().sort("timestamp", -1).limit(10))
        for log in logs:
            log["_id"] = str(log["_id"])
            
        # Get count of auto-processed issues
        auto_count = issues_collection.count_documents({"autonomous_action": "Processed"})
        
        return jsonify({
            "success": True,
            "auto_processed_total": auto_count,
            "recent_actions": logs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/audio/<filename>", methods=['GET'])
def serve_audio(filename):
    """Serve audio files"""
    audio_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'audio')
    try:
        return send_from_directory(audio_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "Audio file not found"}), 404
