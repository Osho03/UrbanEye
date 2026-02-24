import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_ai_summary():
    # 1. Get all issues (Admin endpoint)
    # We use the public one or admin one, doesn't matter for fetching IDs
    try:
        print("1. Fetching Issues...")
        res = requests.get(f"{BASE_URL}/admin/issues")
        if res.status_code != 200:
            print(f"❌ Failed to fetch issues: {res.status_code}")
            return
        
        issues = res.json()
        if not issues:
            print("❌ No issues found in DB.")
            return
            
        latest_issue = issues[0]
        issue_id = latest_issue.get("issue_id") or latest_issue.get("_id")
        print(f"✅ Found latest issue: {issue_id}")
        
        # 2. Test AI Summary Endpoint
        # The frontend calls: /issues/<id>/ai-summary
        target_url = f"{BASE_URL}/issues/{issue_id}/ai-summary"
        print(f"2. Requesting AI Summary from: {target_url}")
        
        summary_res = requests.get(target_url)
        
        if summary_res.status_code == 200:
            print("✅ SUCCESSS! API Returned:")
            print(json.dumps(summary_res.json(), indent=2))
        else:
            print(f"❌ FAILED: {summary_res.status_code}")
            print(summary_res.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_ai_summary()
