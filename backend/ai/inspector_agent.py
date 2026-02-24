"""
UrbanEye AI - Virtual City Inspector Agent
This module acts as a decision support agent for government admins.
It analyzes issue data to providing explainable priority scores and summaries.
"""

def generate_inspection_summary(issue):
    """
    Generates a comprehensive AI inspection report for a given issue.
    """
    if not issue:
        return {"error": "Issue not found"}

    # Extract Key Metrics
    issue_type = issue.get("issue_type", "unknown")
    severity = issue.get("severity_score", 0)
    support = issue.get("support_count", 1) # Default to 1 (the reporter)
    confidence = issue.get("confidence", 0.85) # Mock if missing
    
    # ---------------------------------------------------------
    # 1. AI PRIORITY SCORING ENGINE
    # Transparent Logic: Severity (40%) + Support (30%) + Zones (30%)
    # ---------------------------------------------------------
    
    # Base Score from Severity (0-10 -> 0-40 points)
    score_severity = (severity / 10) * 40
    
    # Public Pressure Score (1-10 reports -> 0-30 points)
    # Cap support at 10 for max score
    capped_support = min(support, 10)
    score_support = (capped_support / 10) * 30
    
    # Context/Zone Score (Mocked - In real app, check GIS layers)
    # We'll assume "potholes" and "garbage" in high numbers are risky
    is_sensitive = False
    if issue_type in ["pothole", "garbage"] and support > 5:
        is_sensitive = True
        
    score_context = 30 if is_sensitive else 0
    
    # Total Priority Score
    priority_score = int(score_severity + score_support + score_context)
    priority_score = min(priority_score, 100) # Cap at 100

    # ---------------------------------------------------------
    # 2. SUGGESTED ACTIONS
    # ---------------------------------------------------------
    if priority_score >= 80:
        suggested_action = "🚨 Immediate Dispatch (High Priority)"
        dispatch_level = "Critical"
    elif priority_score >= 50:
        suggested_action = "📅 Schedule Inspection (Standard)"
        dispatch_level = "Standard"
    else:
        suggested_action = "⏳ Monitor / Verify Later"
        dispatch_level = "Low"

    # ---------------------------------------------------------
    # 3. EXPLAINABLE AI ("WHY?")
    # ---------------------------------------------------------
    explanations = []
    
    if severity >= 7:
        explanations.append(f"• Artificial Intelligence detected high severity visual patterns ({severity}/10).")
    
    if support > 1:
        explanations.append(f"• {support} citizens have reported/verified this issue.")
        
    if is_sensitive:
        explanations.append("• Location appears to be in a high-density or sensitive zone.")
        
    if not explanations:
        explanations.append("• Basic report. No critical risk factors detected currently.")

    # Voice Script (Natural Language Summary for TTS)
    voice_script = f"Inspector Agent Reporting. This is a {dispatch_level} priority {issue_type}. "
    if priority_score > 70:
        voice_script += f"I have flagged this as urgent because of high severity level {severity} and {support} citizen reports. "
    else:
        voice_script += f"Standard protocol recommended. Severity is {severity}. "
    
    voice_script += f"Suggested action is {suggested_action}."

    return {
        "inspector_id": "AI_AGENT_V1",
        "issue_type": issue_type,
        "priority_score": priority_score,
        "priority_breakdown": {
            "severity_contribution": int(score_severity),
            "public_pressure_contribution": int(score_support),
            "zone_risk_contribution": int(score_context)
        },
        "suggested_action": suggested_action,
        "explanations": explanations,
        "voice_script": voice_script,
        "analysis_timestamp": datetime.now().isoformat()
    }

from datetime import datetime
