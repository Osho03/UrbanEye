# Image Serving - Admin Dashboard Feature

## ✅ What Was Added

### Backend Changes

#### 1. Image Serving Endpoint
**File:** `backend/app.py`

Added endpoint to serve uploaded images:
```python
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)
```

**Access images via:**
```
http://127.0.0.1:5000/uploads/pathhole.jpg
http://127.0.0.1:5000/uploads/garbage.png
```

#### 2. Store Image Path in MongoDB
**File:** `backend/routes/issue.py`

Now stores `image_path` in MongoDB:
```python
issue = {
    "title": data.get("title"),
    "description": data.get("description"),
    "latitude": data.get("latitude"),
    "longitude": data.get("longitude"),
    "issue_type": issue_type,
    "image_path": image_path,  # ← NEW: Store image path
    "status": "Pending"
}
```

#### 3. Fixed AI Classifier
Now passes full image path (not just filename) to classifier for actual pixel analysis.

---

## 🎯 How It Works

### Complete Flow

```
1. User uploads image
   ↓
2. Backend saves to uploads/pathhole.jpg
   ↓
3. MongoDB stores: "image_path": "uploads/pathhole.jpg"
   ↓
4. Admin fetches issues from /api/issues/all
   ↓
5. Frontend converts path to URL:
   "http://127.0.0.1:5000/uploads/pathhole.jpg"
   ↓
6. Admin sees image preview in dashboard
```

---

## 📊 MongoDB Document Example

```json
{
  "title": "Broken road",
  "description": "Large pothole on Main Street",
  "latitude": "11.01",
  "longitude": "76.95",
  "issue_type": "pothole",
  "image_path": "uploads/pathhole.jpg",  ← Image path stored
  "status": "Pending"
}
```

---

## 🧪 How to Test

### Step 1: Submit Issue with Image
1. Open http://localhost:3000
2. Fill form and upload image
3. Submit

### Step 2: Get Issue Data
Open: http://localhost:5000/api/issues/all

You'll see:
```json
{
  "image_path": "uploads/pathhole.jpg"
}
```

### Step 3: View Image Directly
Open: http://127.0.0.1:5000/uploads/pathhole.jpg

The image will display in browser!

---

## 🎨 Frontend Integration (Future)

To display images in admin dashboard:

```javascript
// Get issues
const issues = await axios.get("http://localhost:5000/api/issues/all");

// For each issue with image
issues.data.forEach(issue => {
  if (issue.image_path) {
    const imageUrl = `http://127.0.0.1:5000/${issue.image_path}`;
    // Display in <img src={imageUrl} />
  }
});
```

---

## ✅ Benefits

1. **Images are accessible** via URL
2. **Image path stored** in MongoDB
3. **Admin can view** uploaded images
4. **Industry standard** approach
5. **Ready for dashboard** integration

---

## 🚀 Next Steps (Optional)

For a complete admin dashboard:
1. Create admin page at `/admin`
2. Fetch all issues from API
3. Display in table/cards with:
   - Title, description, location
   - Issue type (AI-detected)
   - **Image preview** using stored path
   - Status

**The foundation is now complete!** Images are viewable and ready for admin dashboard integration.
