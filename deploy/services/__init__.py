from .proxy import *
from .database import *
from .cache import *
from .gunicorn import *
from .uwsgi import *
from .project import *
from .celery import *
from .celery_beat import *
from .asgi import ASGIService

enabled = [
    ProxyService,
    CacheService,
    DatabaseService,
    ProjectService,

    CeleryService,
    CeleryBeatService,

    ASGIService,
    
    #GunicornService,
    UWSGIService,
]
