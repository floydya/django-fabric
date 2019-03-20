from fabric import api

from .base import Service


__all__ = (
    'WSGIService',
)


class WSGIService(Service):
    name = 'gunicorn'
    type = 'wsgi'
    is_global_service = False

    def __init__(self, server: 'Server'):
        self.server = server
        self.alias = self.name

    def install(self):
        with self.server.project.source_virtualenv():
            api.run(f'pip install gunicorn gevent')

    def soft_restart(self):
        api.sudo(f'supervisorctl restart {self.alias}')

    def configure(self):
        service_settings = self._render_config(
            'blueprints/conf/gunicorn.py',
            PROJECT_NAME=self.alias
        )
        self.server.create_directory(
            f"{self.server.project.root_path / 'confs'}",
            self.server.project.user
        )

        self.server.copy(
            service_settings,
            'gunicorn.py',
            self.server.project.root_path / 'confs'
        )

        config = self._render_config(
            'blueprints/supervisor/gunicorn.conf',
            PROJECT_NAME=self.alias,
            PATH_TO_PROJECT=self.server.project.working_dir_path,
            PATH_TO_ENV=self.server.project.env_path,
            DJANGO_SOCKETS_PATH=f'/run/{self.server.project.alias}',
            USER=self.server.project.user,
            ALIAS=self.alias
        )
        self.server.copy(
            config, f'{self.alias}.conf', '/etc/supervisor/conf.d'
        )

        api.sudo(f'mkdir -p /run/{self.server.project.alias}')
        api.sudo(f'chown -R {self.server.project.user}:{self.server.project.user} /run/{self.server.project.alias}')
        api.sudo(f'chmod -R 777 /run/{self.server.project.alias}')

        api.sudo(f'supervisorctl reread')
        api.sudo(f'supervisorctl update')
