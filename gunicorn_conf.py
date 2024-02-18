import multiprocessing

# Server socket
bind = "0.0.0.0:8080"  # Bind to all interfaces on port 8000
backlog = 2048  # The maximum number of pending connections

# Worker processes
workers = 3  # Number of worker processes
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn workers
threads = 2  # Number of threads per worker
worker_connections = 1000  # The maximum number of simultaneous clients
timeout = 40  # Workers silent for more than this many seconds are killed and restarted
keepalive = 2  # The number of seconds to wait for requests on a Keep-Alive connection

# Security
limit_request_line = 4094  # The maximum size of HTTP request line in bytes
limit_request_fields = 100  # Limit the number of HTTP headers fields in a request


# Debugging
reload = True  # Restart workers when code changes (not recommended in production)
spew = False  # Install a trace function that spews every line of Python that is executed


# Logging
accesslog = "logs/access.log"  # Access log file
errorlog = "logs/error.log"  # Error log file
loglevel = "info"  # Logging level
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "REPORT_SERVER"


# Server hooks
def on_starting(server):
    print("Starting FastAPI app...")


def on_exit(server):
    print("Stopping FastAPI app...")
