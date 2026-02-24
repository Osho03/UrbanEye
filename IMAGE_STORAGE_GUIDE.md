# 📁 Image Storage Guide - UrbanEye AI

## Where Are Images Stored?

### File System Storage

**Location:** `d:\UrbanEye\backend\uploads\`

All uploaded and camera-captured images are stored in this directory.

**File naming:**
- **File uploads:** Original filename (e.g., `pathhole.jpg`, `garbage.png`)
- **Camera captures:** `camera-capture.jpg` (overwrites each time)

---

## Current Storage Structure

```
d:\UrbanEye\
└── backend\
    └── uploads\           ← All images stored here
        ├── pathhole.jpg
        ├── garbage.png
        ├── osho.jfif
        ├── camera-capture.jpg
        └── ... (more images)
```

---

## How to Access Images

### 1. Via File Explorer
```
Navigate to: d:\UrbanEye\backend\uploads\
```
All images are directly accessible in this folder.

---

### 2. Via Browser (Image Serving Endpoint)
```
http://127.0.0.1:5000/uploads/pathhole.jpg
http://127.0.0.1:5000/uploads/garbage.png
http://127.0.0.1:5000/uploads/camera-capture.jpg
```

The backend serves images via the `/uploads/<filename>` endpoint.

---

### 3. Via MongoDB (Metadata)

**Database:** `urbaneye`  
**Collection:** `issues`

Each issue document contains:
```json
{
  "title": "Civic Issue Report",
  "description": "Reported via UrbanEye AI",
  "latitude": "11.016234",
  "longitude": "76.955678",
  "issue_type": "pothole",
  "image_path": "uploads/pathhole.jpg",  ← Path to image
  "status": "Pending"
}
```

The `image_path` field stores the relative path to the image.

---

## Video Support (Future - Phase 1 Extension)

**Current Status:** ❌ Not implemented yet

**When implemented:**
- Videos will also be stored in `uploads/` directory
- Supported formats: MP4, WebM
- Same serving endpoint: `/uploads/<video-filename>`
- MongoDB will store `video_path` field

**To add video support:**
1. Update frontend to accept video files
2. Add video compression (optional)
3. Backend already handles any file type in `uploads/`

---

## Storage Best Practices

### Current Setup (Development)
- ✅ Images stored locally in `uploads/`
- ✅ Simple and fast for development
- ✅ Easy to access and debug

### Production Recommendations
For a production deployment, consider:

1. **Cloud Storage (AWS S3, Azure Blob, Google Cloud Storage)**
   - Scalable storage
   - CDN integration
   - Automatic backups
   - Cost-effective

2. **File Naming Strategy**
   - Use UUIDs instead of original filenames
   - Prevents overwrites
   - Example: `a3b8d1b6-0b3b-4b1a-9c1a-1a2b3c4d5e6f.jpg`

3. **Image Optimization**
   - Compress images before storage
   - Generate thumbnails
   - Reduce storage costs

---

## How Images Flow Through the System

### Upload Flow
```
1. User captures/uploads image
   ↓
2. Frontend sends to backend via FormData
   ↓
3. Backend saves to: d:\UrbanEye\backend\uploads\
   ↓
4. Backend stores path in MongoDB: "uploads/filename.jpg"
   ↓
5. AI analyzes image from uploads/ directory
   ↓
6. Admin can view via: http://127.0.0.1:5000/uploads/filename.jpg
```

### Training Flow
```
1. Admin verifies issues in MongoDB
   ↓
2. Run: python ai/prepare_dataset.py
   ↓
3. Script copies images from uploads/ to ai/dataset/<class>/
   ↓
4. Images organized by issue type:
   - ai/dataset/pothole/
   - ai/dataset/garbage/
   - ai/dataset/water_leak/
   - ai/dataset/streetlight/
   ↓
5. Run: python ai/train_model.py
   ↓
6. Model trained on organized dataset
```

---

## Checking Your Images

### Via Command Line
```powershell
# List all images in uploads/
cd d:\UrbanEye\backend
Get-ChildItem uploads

# Count total images
(Get-ChildItem uploads).Count

# Check total size
(Get-ChildItem uploads | Measure-Object -Property Length -Sum).Sum / 1MB
```

### Via MongoDB Compass
1. Connect to `mongodb://localhost:27017`
2. Database: `urbaneye`
3. Collection: `issues`
4. Each document shows `image_path` field

### Via Browser
1. Get all issues: http://localhost:5000/api/issues/all
2. Find `image_path` in JSON response
3. View image: http://127.0.0.1:5000/uploads/[filename]

---

## Important Notes

### Camera Capture Filename Issue
> [!WARNING]
> **Current Limitation**: Camera captures always use `camera-capture.jpg`
> 
> This means each camera capture **overwrites** the previous one in the filesystem.
> 
> **However**, MongoDB still stores the correct reference, and the AI processes the image before it's overwritten.
> 
> **Fix for Phase 2**: Generate unique filenames using timestamps or UUIDs:
> ```javascript
> const filename = `camera-${Date.now()}.jpg`;
> ```

### Storage Limits
- **Development**: No limits (local disk space)
- **Production**: Implement storage quotas and cleanup policies

### Backup
- **Current**: No automatic backup
- **Recommendation**: Regular backups of `uploads/` directory and MongoDB

---

## Quick Commands

### View all images
```powershell
explorer d:\UrbanEye\backend\uploads
```

### Count images
```powershell
(Get-ChildItem d:\UrbanEye\backend\uploads).Count
```

### View latest image
```powershell
Get-ChildItem d:\UrbanEye\backend\uploads | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### Open image in browser
```
http://127.0.0.1:5000/uploads/pathhole.jpg
```

---

## Summary

**Images are stored in:** `d:\UrbanEye\backend\uploads\`

**Access methods:**
1. File Explorer: `d:\UrbanEye\backend\uploads\`
2. Browser: `http://127.0.0.1:5000/uploads/<filename>`
3. MongoDB: `image_path` field in `issues` collection

**Video support:** Not yet implemented (planned for future)

**For production:** Consider cloud storage (S3, Azure Blob, etc.)
