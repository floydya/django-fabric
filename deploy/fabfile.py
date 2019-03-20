import sys, pathlib, os
from fabric import api, contrib

sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
sys.path.append(str(pathlib.Path(__file__).parent.parent))
sys.path.append(str(pathlib.Path(__file__).parent))

from deploy import server, services

api.env.hosts = [os.environ['DEPLOY_IP']]
api.env.user = 'root'
api.env.key_filename = os.environ['DEPLOY_KEY']


@api.task
def pull():
    server.project.pull()


@api.task
def migrate():
    server.project.migrate()


@api.task
def collectstatic():
    server.project.collectstatic()


@api.task
def makemessages():
    server.project.makemessages()


@api.task
def update_project():
    server.project.update()
    server.project.restart()

    if hasattr(server, 'celery'):
        server.celery.restart()

    if hasattr(server, 'celery_beat'):
        server.celery_beat.restart()

    server.proxy.restart()


@api.task
def configure(service: str=None):
    if not service:
        server.install()
        return

    service = server.get_service(service)

    if not service:
        raise AttributeError

    service.install()
    service.configure()


@api.task
def restart(service: str=None):
    service = server.get_service(service)

    if not service:
        raise AttributeError(f'No service `{service}`')

    service.soft_restart()


@api.task
def restart_server(service=None):
    api.sudo('reboot')


@api.task
def status(service: str) -> str:
    service = server.get_service(service)

    if not service:
        raise AttributeError(f'No service `{service}`')

    service.status()
