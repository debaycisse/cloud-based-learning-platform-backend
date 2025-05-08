# gunicorn_config.py
import multiprocessing

# Bind to this socket
bind = "0.0.0.0:8000"

# Number of worker processes
# A common formula is: (2 x $num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout in seconds
timeout = 120

# Log level
loglevel = "info"

# Access log file
accesslog = "logs/access.log"

# Error log file
errorlog = "logs/error.log"

# Process name
proc_name = "learning_platform"

# Preload application code before forking worker processes
preload_app = True

# Restart workers after this many requests
max_requests = 1000

# Restart workers after this many seconds
max_requests_jitter = 50
