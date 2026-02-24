# Where Are Your Uploaded Photos?

## Photo Storage Location

All uploaded images are saved in:
```
d:\UrbanEye\backend\uploads\
```

## How to View Your Photos

### Option 1: File Explorer
1. Open File Explorer
2. Navigate to: `D:\UrbanEye\backend\uploads`
3. You'll see all uploaded images there

### Option 2: Command Line
```powershell
cd D:\UrbanEye\backend\uploads
dir
```

## What's Stored in MongoDB

Looking at your MongoDB Compass screenshot, I can see the database stores:
- `title` - Issue title
- `description` - Issue description
- `latitude` and `longitude` - Location coordinates
- `issue_type` - AI-detected type (pothole, garbage, water_leak, streetlight, unknown)
- `status` - Current status (Pending)

**Note:** The actual image file is NOT stored in MongoDB - only the metadata is stored. The image file itself is saved in the `uploads/` folder on disk.

## Why Images Aren't in MongoDB

This is a **best practice** for handling file uploads:
- ✅ **MongoDB stores:** Metadata (title, description, location, issue_type)
- ✅ **File system stores:** Actual image files (in `uploads/` folder)
- 💡 **Reason:** Storing large binary files in databases is inefficient

## How to Link Images to Issues (Future Enhancement)

For Day-3+, we could add:
1. Store the image filename in MongoDB
2. Create an API endpoint to serve images
3. Display images in the frontend

Example MongoDB document would include:
```json
{
  "title": "pothole",
  "description": "pothole is present in the road",
  "latitude": "11.01",
  "longitude": "76.95",
  "issue_type": "unknown",
  "status": "Pending",
  "image_filename": "pothole.jpg"  ← Add this
}
```

Then create an endpoint like:
```
GET /api/issues/image/<filename>
```

## Current Setup (Day-2)

Right now:
- ✅ Images are uploaded successfully
- ✅ Images are saved to `backend/uploads/`
- ✅ AI classifier analyzes the filename
- ✅ Issue metadata is stored in MongoDB
- ⚠️ Image filename is NOT stored in MongoDB (yet)
- ⚠️ No way to retrieve/display images in UI (yet)

This is normal for Day-2 - we focused on getting the upload pipeline working!
