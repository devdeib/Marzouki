"""
Gunicorn configuration for the Marzouki Django app.

Reference: https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8001")

workers = int(os.environ.get(
    "GUNICORN_WORKERS",
    max(2, multiprocessing.cpu_count() * 2 + 1),
))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.environ.get("GUNICORN_THREADS", 4))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", 60))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))

# Recycle workers periodically to mitigate memory leaks.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 50))

accesslog = os.environ.get("GUNICORN_ACCESSLOG", "-")  # stdout
errorlog = os.environ.get("GUNICORN_ERRORLOG", "-")  # stderr
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Trust the X-Forwarded-* headers from the reverse proxy (Nginx).
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "127.0.0.1")
proxy_allow_ips = forwarded_allow_ips
