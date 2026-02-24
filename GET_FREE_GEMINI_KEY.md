# 🎉 **Get Your FREE Google Gemini API Key** 🎉

## Why Gemini?
- ✅ **100% FREE** - No billing required!
- ✅ **Generous limits** - 60 requests/minute FREE tier
- ✅ **Better responses** - Real AI, not rule-based
- ✅ **Fast** - Gemini 1.5 Flash is optimized for speed
- ✅ **No credit card needed**

---

## 📝 **How to Get Your FREE Key (2 minutes)**

### Step 1: Visit Google AI Studio
Go to: **https://makersuite.google.com/app/apikey**

Or: **https://aistudio.google.com/app/apikey**

### Step 2: Sign In
- Use your Google account (Gmail)
- No payment info required!

### Step 3: Create API Key
1. Click **"Create API Key"**
2. Choose **"Create API key in new project"** (or select existing)
3. Copy your API key (starts with `AIza...`)

### Step 4: Add to UrbanEye
1. Open: `d:\UrbanEye\backend\.env`
2. Replace this line:
   ```
   GEMINI_API_KEY=
   ```
   With:
   ```
   GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXX
   ```
3. Save the file

### Step 5: Restart Backend
```powershell
# Stop current backend (Ctrl+C)
cd d:\UrbanEye\backend
py -3.13 app.py
```

---

## ✅ **Done!**

You should see:
```
✅ Using Google Gemini AI (FREE tier)
✅ Chatbot routes registered
```

Now test the chatbot:
- Open: http://localhost:3000
- Click purple 💬 button
- Ask: "How do I report a pothole?"
- Get REAL AI responses! 🚀

---

## 🆓 **Free Tier Limits**

**Gemini 1.5 Flash (FREE forever):**
- 15 requests per minute
- 1 million requests per day
- 1,500 requests per day (free tier)

**More than enough for testing and small deployments!**

---

## 📚 **Documentation**

- Gemini API Docs: https://ai.google.dev/docs
- Free tier info: https://ai.google.dev/pricing

---

**Any questions? Just ask! The FREE Gemini API gives you REAL AI chatbot without any cost!** 🎊
