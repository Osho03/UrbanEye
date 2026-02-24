# MongoDB Manual Installation Guide for Windows

## Quick Install Steps

### Step 1: Download MongoDB
1. Open this link in your browser: **https://www.mongodb.com/try/download/community**
2. Select:
   - **Version:** 8.0.4 (current)
   - **Platform:** Windows
   - **Package:** MSI
3. Click **Download**

### Step 2: Install MongoDB
1. Run the downloaded `.msi` file
2. Click **Next** through the wizard
3. Accept the license agreement
4. Choose **Complete** installation type
5. **IMPORTANT:** On "Service Configuration" screen:
   - ✅ Check "Install MongoDB as a Service"
   - ✅ Check "Run service as Network Service user"
   - Leave "Service Name" as `MongoDB`
   - Leave "Data Directory" as default
   - Leave "Log Directory" as default
6. **OPTIONAL:** Uncheck "Install MongoDB Compass" (GUI tool, not needed for now)
7. Click **Install**
8. Wait for installation to complete
9. Click **Finish**

### Step 3: Verify MongoDB is Running

Open PowerShell and run:
```powershell
# Check if MongoDB service is running
Get-Service MongoDB
```

You should see:
```
Status   Name               DisplayName
------   ----               -----------
Running  MongoDB            MongoDB
```

If it says "Stopped", start it:
```powershell
net start MongoDB
```

### Step 4: Test the Connection

```powershell
cd D:\UrbanEye\backend
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe test_mongodb.py
```

You should see:
```
✅ SUCCESS: MongoDB is running and connected!
```

### Step 5: Start Your Backend

```powershell
cd D:\UrbanEye\backend
start.bat
```

---

## Alternative: MongoDB Without Service (Manual Start)

If you prefer NOT to install as a service:

### 1. Create data directory
```powershell
mkdir C:\data\db
```

### 2. Start MongoDB manually
```powershell
# This will keep running - don't close this terminal
mongod
```

### 3. In a NEW terminal, test connection
```powershell
cd D:\UrbanEye\backend
C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe test_mongodb.py
```

---

## Troubleshooting

### Error: "MongoDB service not found"
- MongoDB was not installed as a service
- Use the manual start method above

### Error: "Access denied" when starting service
- Open PowerShell as Administrator
- Run: `net start MongoDB`

### Error: "Port 27017 already in use"
- Another instance of MongoDB is running
- Check Task Manager and close any `mongod.exe` processes

---

## After MongoDB is Running

Once you see `✅ SUCCESS: MongoDB is running and connected!`, proceed with:

### Terminal 1 - Backend
```powershell
cd D:\UrbanEye\backend
start.bat
```

### Terminal 2 - Frontend
```powershell
cd D:\UrbanEye\frontend
npm start
```

Then open **http://localhost:3000** in your browser!
