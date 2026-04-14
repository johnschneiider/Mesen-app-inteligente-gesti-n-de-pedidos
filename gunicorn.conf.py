"""
Gunicorn configuration for Mesenú production.
Reference: https://docs.gunicorn.org/en/stable/settings.html
"""
import multiprocessing
import os

# ── Binding ──────────────────────────────────────────────────────────────────
bind = "127.0.0.1:8005"

# ── Workers ──────────────────────────────────────────────────────────────────
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"   # ASGI (handles WebSockets)
timeout = 60
keepalive = 5

# ── Logging ──────────────────────────────────────────────────────────────────
accesslog  = "/var/www/mesenu/mesenu/logs/gunicorn-access.log"
errorlog   = "/var/www/mesenu/mesenu/logs/gunicorn-error.log"
loglevel   = "warning"

# ── Environment ───────────────────────────────────────────────────────────────
# Force production settings regardless of the systemd EnvironmentFile
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.settings.production",
]
