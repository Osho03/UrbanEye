# 🚀 UrbanEye AI - Quick Start Guide

## ✅ Application is Running!

Both servers are active and ready:

### Backend (with MobileNetV2 AI)
- **URL:** http://127.0.0.1:5000
- **Status:** ✅ Running
- **AI Model:** MobileNetV2 loaded successfully
- **Features:** Real computer vision, image classification

### Frontend (React)
- **URL:** http://localhost:3000
- **Status:** ✅ Running
- **Features:** Professional UI, image upload, issue reporting

### Database (MongoDB)
- **Status:** ✅ Connected
- **Database:** urbaneye
- **Collection:** issues

---

## 🎯 How to Use the Application

### Step 1: Open the Application
The application should open automatically in your browser at:
**http://localhost:3000**

If not, manually open your browser and navigate to that URL.

### Step 2: Submit a Civic Issue

You'll see a clean white card with:
- **Title field** - Enter issue title (e.g., "Broken road on Main Street")
- **Description field** - Enter details (e.g., "Large pothole causing traffic issues")
- **File upload** - Click "Choose File" and select any image
- **Submit button** - Blue button to submit

### Step 3: Upload and Submit

1. Fill in the title and description
2. **Upload ANY image** - The AI will analyze the actual image content
3. Click "Submit Issue"
4. You'll see an alert with the detected issue type

**Important:** The AI now analyzes the actual image pixels using MobileNetV2, not the filename!

### Step 4: View All Issues

Open in browser: **http://localhost:5000/api/issues/all**

You'll see all submitted issues in JSON format with:
- title
- description
- latitude & longitude
- **issue_type** (detected by AI)
- status

---

## 🧪 Testing the Computer Vision

### Test with Different Images

Try uploading various images to see how the AI classifies them:

1. **Road/pavement images** → May detect as "pothole"
2. **Trash/waste images** → May detect as "garbage"
3. **Water/liquid images** → May detect as "water_leak"
4. **Light/lamp images** → May detect as "streetlight"
5. **Random images** → Will return "unknown" if confidence < 0.5

### What to Expect

- **Confidence threshold:** AI needs ≥ 50% confidence to classify
- **Low confidence:** Returns "unknown" for ambiguous images
- **Processing time:** 1-2 seconds per image (after initial load)
- **Accuracy:** Moderate (needs fine-tuning for production)

---

## 📊 Check Your Data

### View in MongoDB Compass

1. Open MongoDB Compass
2. Connect to: `mongodb://localhost:27017`
3. Navigate to: `urbaneye` → `issues`
4. See all submitted issues with AI-detected types

### View Uploaded Images

All uploaded images are saved in:
```
D:\UrbanEye\backend\uploads\
```

Open this folder in File Explorer to see all uploaded photos.

---

## 🛑 How to Stop the Application

### Stop Backend
- Go to the backend terminal
- Press `Ctrl + C`

### Stop Frontend
- Go to the frontend terminal
- Press `Ctrl + C`

### Stop MongoDB (Optional)
```powershell
net stop MongoDB
```

---

## 🔄 How to Restart

### Start MongoDB (if stopped)
```powershell
net start MongoDB
```

### Start Backend
```powershell
cd D:\UrbanEye\backend
.\start.bat
```

### Start Frontend
```powershell
cd D:\UrbanEye\frontend
npm start
```

---

## 📝 Current Features

### Day-1 ✅
- Flask backend API
- MongoDB database
- React frontend
- Complete data pipeline

### Day-2 ✅
- Image upload functionality
- Professional UI design
- FormData submission
- Image storage

### Day-3 ✅
- **Real computer vision** with MobileNetV2
- **Actual image analysis** (not filename-based)
- **Confidence-based classification**
- **Deep learning integration**

---

## 🎉 You're All Set!

The application is fully functional with real AI-powered image classification. Upload images and watch the computer vision model analyze them in real-time!

**Frontend:** http://localhost:3000  
**Backend API:** http://127.0.0.1:5000  
**View All Issues:** http://localhost:5000/api/issues/all

Enjoy testing your Smart City civic issue reporting platform! 🚀
