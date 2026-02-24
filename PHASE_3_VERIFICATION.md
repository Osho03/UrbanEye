# ✅ Phase 3 Verification Workflow: Citizen User Loop

This guide explains how to verify the **"My Reports"** feature, which allows citizens to track their submitted issues without logging in.

---

## 🧪 Option 1: Manual Browser Testing
**Best for visual verification.**

### Step 1: Open Citizen App
1. Navigate to: [http://localhost:3000](http://localhost:3000)
2. You should see two tabs at the top: **"Report Issue"** and **"My Reports"**.

### Step 2: Submit a New Report
1. Stay on the **"Report Issue"** tab.
2. Click **"📷 Camera"** (or Upload) to capture an image.
3. (Optional) Enter a title like "Test Pothole".
4. Click **"🚀 Submit Report"**.
5. Wait for the success alert: *"Issue reported! Detected type: ..."*

### Step 3: Check "My Reports"
1. The app should automatically switch to the **"My Reports"** tab (or click it manually).
2. **Verify:** You should see your new issue listed card.
   - **Status:** Should be **"Pending"** (Yellow badge).
   - **Date:** Today's date.
   - **Type:** The AI-detected issue type.

### Step 4: Verify Persistence
1. **Refresh the page** (F5).
2. Go back to **"My Reports"**.
3. **Verify:** The issue should still be there! (It is saved in your browser's Local Storage).

---

## ⚙️ Option 2: Admin Workflow Integration
**Verify real-time status updates.**

1. Keep the **Citizen App** open on "My Reports" (Status: **Pending**).
2. Open **Admin Dashboard** in a new tab: [http://localhost:3001](http://localhost:3001) (Login: `admin` / `admin123`).
3. Find the issue you just reported in **"Issue Management"**.
4. Click **"View Details"**.
5. Change Status to **"Assigned"** and add a remark (e.g., "Team dispatched").
6. Go back to **Citizen App** and refresh.
7. **Verify:**
   - Status badge should change to **"Assigned"** (Blue).
   - Admin Remark should appear on the card.

---

## 🤖 Option 3: Automated Script
**Verify API data flow instantly.**

Run the verification script in your terminal:

```bash
cd d:\UrbanEye\backend
python test_myreports_flow.py
```

**Expected Output:**
```
Step 1: Reporting Issue...
✅ Reported! ID: [unique_id]
Step 2: Checking Status API...
✅ Status Fetched!
...
✅ Verification Passed: Issue is Pending
```
