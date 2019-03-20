"""gunicorn WSGI server configuration."""
from multiprocessing import cpu_count


def get_max_workers():
    return cpu_count() * 2 + 1


def get_max_treads():
    """
    Returns amount of worker threads to handle requests
    By default - 1. Generally its 2-4 * ($NUM_CORES).
    Requires testing per project
    """
    return cpu_count()


max_requests = 1000
worker_class = 'gevent'
workers = get_max_workers()
threads = get_max_treads()
