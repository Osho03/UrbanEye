# 🏛️ Government Admin Dashboard - User Guide

## 🎯 Purpose
The Admin Dashboard is a secure, internal government interface used by municipal authorities to view, verify, and resolve citizen-reported civic issues. It is completely separate from the public reporting app.

---

## 🔐 Access & Authentication

**URL:** [http://localhost:3001](http://localhost:3001)

**Authorized Personnel Only:**
- **Username:** `admin`
- **Password:** `admin123`

> [!WARNING]
> This dashboard is for official use only. Do not share credentials.

---

## 🖥️ Dashboard Modules

### 1. Dashboard Overview
**Real-time situational awareness:**
- **Total stats cards:** Total, Pending, Assigned, Resolved
- **Issues by Type:** Pie chart showing distribution (pothole vs garbage etc.)
- **Resolution Status:** Bar chart tracking workflow progress

### 2. Issue Management
**Central command for all reports:**
- **Table View:** Sortable list of all issues with status badges
- **Filters:** Filter by status (Pending, Assigned, Resolved)
- **Search:** Find issues by type or description
- **Quick Actions:** Button to view full details

### 3. Issue Detail View
**Deep dive into specific reports:**
- **📸 Visual Evidence:** Large view of uploaded image
- **🧠 AI Analysis:**
  - Detected Issue Type
  - Confidence Score
  - Severity Estimate (AI)
- **📋 Metadata:** Location, timestamp, assigned department
- **🛡️ Admin Actions:**
  - **Verify:** Mark AI prediction as Correct ✅ or Incorrect ❌
  - **Status:** update workflow (Assign → In Progress → Resolve)
  - **Remarks:** Add internal notes for other officials

---

## 🔁 Workflow Guide

1. **Login** to Dashboard.
2. Review **Overview** for high-priority alerts.
3. Go to **Issue Management** list.
4. Open a **Pending** issue.
5. **Verify** the image matches the AI-detected type.
   - If correct, click "Verify as Correct".
   - If wrong, click "Mark Incorrect" and correct it.
6. **Update Status** to "Assigned".
   - The system auto-assigns the department (e.g., Pothole → Road Dept).
7. Once work is done, mark as **Resolved**.

---

## 🧩 Technical Architecture

- **Frontend:** React (separate app on port 3001)
- **Backend:** Flask (shared API on port 5000)
- **Database:** MongoDB (shared `issues` collection)
- **Security:** JWT-based stateless authentication (Phase 3 planned)

---

## 🚀 Next Phase (Phase 2B/C)
- **Maps:** Geospatial view of issues on a city map.
- **Routing:** Advanced auto-assignment logic.
- **Analytics:** Exportable PDF reports.
