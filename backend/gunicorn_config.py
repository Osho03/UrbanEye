import multiprocessing
import os

# Gunicorn Configuration for High Concurrency & Stability
# Designed for UrbanEye Million-Scale Civic Operations

# Bind to 0.0.0.0 for external access (Render/Heroku/Docker)
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Workers: Number of concurrent processes
# Recommended: (2 x cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

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
