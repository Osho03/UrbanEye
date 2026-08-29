# Deploy UrbanEye to Hugging Face Spaces (free, NO credit card)

Hugging Face Spaces gives you a Linux server with 2 CPU / 16 GB RAM for free.
That is plenty for your trained YOLOv8 model — this is the replacement for Oracle.

Time: ~30 minutes total. Cost: $0. No card at any step.

## Step 1 — Create your Hugging Face account (5 min)

1. Open https://huggingface.co/join
2. Sign up with email + password (do NOT pick a paid plan — free forever).

## Step 2 — Create the Space (3 min)

1. Open https://huggingface.co/new-space
2. Space name: `urbaneye`
3. License: Apache-2.0
4. **SDK: choose `Docker`** (important!)
5. Click **Create Space**.

## Step 3 — Add your secrets (3 min)

1. Inside your Space, go to **Settings → Variables and secrets**
2. Add these two **secret** variables (values stay private, not in the repo):
   - `MONGO_URI` → your Atlas connection string (same one Render used)
   - `GEMINI_API_KEY` → your (new) Gemini key from Google AI Studio
3. Save.

## Step 4 — Get a token (2 min)

1. https://huggingface.co/settings/tokens → **Create new token**
2. Type: **Write** → name it `urbaneye` → create → **copy it**.

## Step 5 — Push the deployment files (5 min)

On your PC, open **PowerShell** in the repo folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File hf_space\push_to_hf.ps1
```

It asks for your Hugging Face **username** and the **token**. It copies the
`Dockerfile` + `README.md` into your Space and pushes them.

## Step 6 — Wait for the build (5–10 min)

1. Open https://huggingface.co/spaces/<your-username>/urbaneye
2. You will see the build logs. Wait for **"Running on ..."** / green.
3. When it is live you also get logs from the app itself.

## Step 7 — Verify the ML works

Test the live endpoint (replace the URL with your username):

```powershell
curl https://<your-username>-urbaneye.hf.space/api/health
```

Then send a real photo and check you get a detection back:

```powershell
curl -X POST https://<your-username>-urbaneye.hf.space/api/issues/report `
  -F "image=@C:\Users\acer\Desktop\urbaneye\UrbanEye\backend\uploads\1770534531_bdc8c662.jpg" `
  -F "title=HF verification" -F "description=test" `
  -F "latitude=12.97" -F "longitude=77.59" -F "address=Bengaluru"
```

A success response contains `"issue_type"` (garbage, pothole, ...) with a real confidence — not `unknown`, not an error.

## Step 8 — Point the app at the new URL

In `mobile/lib/services/api_service.dart` line 18 change to:

```dart
static String baseUrl = 'https://<your-username>-urbaneye.hf.space';
```

Rebuild the APK and install.

## Notes

- **Sleeping:** the free Space sleeps after ~48 h without visitors. First request after waking takes ~1 min (it boots back up automatically).
- **Redeploys:** every time you push code to your GitHub `main`, the Space rebuilds with the latest code (the Dockerfile clones your repo during each build).
- **Your data:** uploaded photos live in MongoDB Atlas (MongoDB free tier) — that part never changes.