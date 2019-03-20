from .services import *
from .server import *

server = Server([service for service in enabled])
