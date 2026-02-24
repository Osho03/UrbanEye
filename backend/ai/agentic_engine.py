import json
import os
from datetime import datetime

# Initialize Gemini (Lazy Load)
model = None

def get_model():
    global model
    if model is None:
        from ai.gemini_chatbot import init_gemini, gemini_chatbot
        if not gemini_chatbot:
            init_gemini()
        model = gemini_chatbot.model
    return model

def run_agentic_pipeline(description, location, image_path=None):
    """
    Executes the 4-step Agency Chain:
    Triage -> Policy -> Assignment -> Verifier
    """
    ai = get_model()
    results = {}
    
    # 1. 🤖 TRIAGE AGENT
    triage_prompt = f"""You are an Autonomous Civic Triage Agent responsible for decision-making in a smart city system.

Your task is to:

1. Validate complaint authenticity
2. Identify civic issue type
3. Assess severity level (1-5)
4. Determine priority (Low/Medium/High/Critical)
5. Recommend responsible department
6. Suggest action deadline

Complaint:
{description}

Location:
{location}

Image Description:
(Image analysis skipped for text-only input, rely on description)

Return structured decision in JSON format:
{{
    "valid_complaint": true/false,
    "issue_type": "string",
    "severity_score": number,
    "priority_level": "string",
    "assigned_department": "string",
    "recommended_deadline": "string"
}}"""

    try:
        print("🤖 AGENT 1: Triage Agent Running...")
        triage_resp = ai.generate_content(triage_prompt)
        # cleanup markdown
        text = triage_resp.text.replace('```json', '').replace('```', '').strip()
        triage_data = json.loads(text)
        results["triage"] = triage_data
    except Exception as e:
        print(f"❌ Triage Failed: {e}")
        triage_data = {"issue_type": "Unknown", "priority_level": "Medium"}
        results["triage"] = {"error": str(e)}

    # 2. ⚖️ POLICY AGENT (RAG)
    policy_prompt = f"""You are a Civic Compliance Officer AI.

Using the municipal policy documents provided (Simulated Knowledge Base),
determine:

1. Relevant law or rule
2. Required resolution time
3. Violation severity

Issue Type:
{triage_data.get('issue_type')}

Location:
{location}

Return JSON:
{{
    "applicable_policy": "string",
    "required_resolution_time": "string",
    "compliance_status": "string"
}}"""

    try:
        print("⚖️ AGENT 2: Policy Agent Running...")
        policy_resp = ai.generate_content(policy_prompt)
        text = policy_resp.text.replace('```json', '').replace('```', '').strip()
        results["policy"] = json.loads(text)
    except Exception as e:
         results["policy"] = {"error": str(e)}

    # 3. 📢 ASSIGNMENT AGENT
    assign_prompt = f"""You are an Autonomous Civic Dispatcher.

Based on issue type and priority,
automatically assign the correct department.

Issue:
{triage_data.get('issue_type')}

Priority:
{triage_data.get('priority_level')}

Return JSON:
{{
    "assigned_department": "string",
    "escalation_required": true/false
}}"""

    try:
        print("📢 AGENT 3: Assignment Agent Running...")
        assign_resp = ai.generate_content(assign_prompt)
        text = assign_resp.text.replace('```json', '').replace('```', '').strip()
        results["assignment"] = json.loads(text)
    except Exception as e:
        results["assignment"] = {"error": str(e)}

    # 4. ✅ VERIFIER AGENT
    # Note: In a report submission flow, we assume the image is "Before" and we don't have "After".
    # We will modify the prompt slightly to assess the "Current Status" based on the single image.
    verifier_prompt = f"""You are a Civic Resolution Verifier AI.

Compare the "Before" and "After" images of a reported civic issue.
(Note: Only initial report image is available. Assess current status.)

Determine if the issue is:
Resolved / Partially Resolved / Not Resolved

Return JSON:
{{
    "resolution_status": "string",
    "quality_of_fix": "string",
    "reopen_ticket_required": true/false
}}"""
    
    try:
        print("✅ AGENT 4: Verifier Agent Running...")
        # Ideally we pass images here, but for text-flow we simulate or skip
        verifier_resp = ai.generate_content(verifier_prompt)
        text = verifier_resp.text.replace('```json', '').replace('```', '').strip()
        results["verification"] = json.loads(text)
    except Exception as e:
        results["verification"] = {"error": str(e)}

    return results
