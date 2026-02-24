# UrbanEye AI - Setup & Troubleshooting Guide

## ⚠️ CURRENT ISSUES IDENTIFIED

### 1. Python Installation Issue
- You have **Python 3.14.0** (broken - missing pip and libraries)
- You have **Python 3.13.9** (working - this is what we'll use)

### 2. MongoDB Not Running
- MongoDB is **NOT currently running** on your system
- You need to install and start MongoDB

---

## 🔧 QUICK FIX - How to Run the Backend

### Option 1: Use the start script (EASIEST)
```bash
cd backend
start.bat
```

### Option 2: Use full Python path
```bash
cd backend
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe app.py
```

---

## 📦 MongoDB Installation & Setup

### Step 1: Check if MongoDB is installed
```bash
mongod --version
```

If you get an error, MongoDB is not installed.

### Step 2: Install MongoDB Community Edition

**Option A: Using Chocolatey (Recommended)**
```bash
# Install Chocolatey first if you don't have it
# Then run:
choco install mongodb
```

**Option B: Manual Download**
1. Go to: https://www.mongodb.com/try/download/community
2. Download MongoDB Community Server for Windows
3. Run the installer
4. Choose "Complete" installation
5. Install MongoDB as a Windows Service (check the box)

### Step 3: Start MongoDB

**If installed as a service:**
```bash
# Start the service
net start MongoDB
```

**If NOT installed as a service:**
```bash
# Create data directory
mkdir C:\data\db

# Start MongoDB manually
mongod
```

### Step 4: Verify MongoDB is running
```bash
cd backend
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe test_mongodb.py
```

You should see: `✅ SUCCESS: MongoDB is running and connected!`

---

## 🚀 Complete Startup Sequence

### Terminal 1 - MongoDB (if not running as service)
```bash
mongod
```
Leave this running.

### Terminal 2 - Backend
```bash
cd backend
start.bat
```
Backend runs on `http://localhost:5000`

### Terminal 3 - Frontend
```bash
cd frontend
npm start
```
Frontend runs on `http://localhost:3000`

---

## ✅ Testing the Connection

### Test MongoDB Connection
```bash
cd backend
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe test_mongodb.py
```

### Test Backend API
Once backend is running, open browser:
- GET all issues: http://localhost:5000/api/issues/all

---

## 🐛 Common Errors & Solutions

### Error: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Use Python 3.13 instead of 3.14
```bash
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe app.py
```

### Error: "Cannot connect to MongoDB"
**Solution:** Start MongoDB first
```bash
# Check if MongoDB service is running
net start MongoDB

# OR start manually
mongod
```

### Error: "Could not find platform independent libraries"
**Solution:** This is Python 3.14 issue - use Python 3.13 instead

---

## 📝 Next Steps After Setup

1. ✅ Install MongoDB
2. ✅ Start MongoDB service
3. ✅ Run `test_mongodb.py` to verify connection
4. ✅ Start backend with `start.bat`
5. ✅ Start frontend with `npm start`
6. ✅ Test the complete pipeline

---

## 💡 Pro Tips

- **Set Python 3.13 as default:** Add `C:\Users\Admin\AppData\Local\Programs\Python\Python313` to your PATH environment variable BEFORE Python 3.14
- **MongoDB as Service:** Install MongoDB as a Windows service so it starts automatically
- **Keep terminals open:** Don't close the terminal windows while the servers are running
