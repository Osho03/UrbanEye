---
title: UrbanEye
emoji: 🏙️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# UrbanEye backend — free Hugging Face Spaces

Detects civic issues (pothole, garbage, water leak, streetlight, drainage, sidewalk damage) with the trained YOLOv8 model.

- App root: `https://<your-username>-urbaneye.hf.space`
- Health check: `GET /api/health`
- Report: `POST /api/issues/report` (multipart `image` + form fields)

## Required secrets

Set these as **private** secrets in Space Settings → Variables and secrets:

| Name | Value |
|---|---|
| `MONGO_URI` | your MongoDB Atlas connection string |
| `GEMINI_API_KEY` | your Gemini API key |

Every code redeploy happens automatically because the Dockerfile pulls the latest `main` from the public GitHub repo on each build.