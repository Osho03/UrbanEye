import multiprocessing
import os

# Gunicorn Configuration for High Concurrency & Stability
# Designed for UrbanEye Million-Scale Civic Operations

# FORCE port 5000 to match Render's scan (Hammer Fix)
bind = "0.0.0.0:5000"

# Workers: Reduced to 2 for Render Free Tier stability
workers = 2

# Worker Class: Use 'gevent' or 'eventlet' for high I/O concurrency 
# (Requires gevent/eventlet in requirements.txt)
# Default is 'sync' which is safer for standard Flask apps
worker_class = "sync"

# Threads: Multiple threads per worker process
threads = 4

# Timeout: Allow up to 120s for AI processing (Gemini latency)
timeout = 120

# Keep-alive: 2s for fast reconnection
keepalive = 2

# Logging: Professional logs for auditing
accesslog = "-" # Stdout
errorlog = "-"  # Stderr
loglevel = "info"

# Security: Limit request size to 10MB (Photos/Videos)
limit_request_line = 4094
limit_request_field_size = 8190
