# ============================================================
# UrbanEye backend on Hugging Face Spaces (free, no credit card)
# The Space repo contains only this file + README.md; the backend
# itself is pulled from the public GitHub repo during the build.
# ============================================================
FROM python:3.11-slim

# System libs: git (to fetch the backend), curl (health checks),
# build essentials + OpenCV runtime libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl gcc g++ make libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Pull the latest UrbanEye backend from GitHub
WORKDIR /app
RUN git clone --depth 1 https://github.com/Osho03/UrbanEye.git /app/backend-src

# Install CPU-only torch FIRST (smaller image, no CUDA), then the
# rest of the backend dependencies from requirements.txt.
WORKDIR /app/backend-src/backend
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Hugging Face expects the app to listen on port 7860
ENV PORT=7860

# Single worker, port 7860 (CLI overrides the 5000 bind in gunicorn_config.py)
CMD ["gunicorn", "-c", "/app/backend-src/backend/gunicorn_config.py", "--chdir", "/app/backend-src/backend", "-b", "0.0.0.0:7860", "app:app"]