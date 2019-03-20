from fabric import api

from .base import Service


__all__ = (
    'ASGIService',
)


class ASGIService(Service):
    name = 'asgi'
    type = 'asgi'
    is_global_service = False
    base_url = '/ws'

    @property
    def sockets_path(self):
        return f'/run/{self.alias}'

    def install(self):
        with self.server.project.source_virtualenv():
            api.run(f'pip install daphne')

    def soft_restart(self):
        api.sudo(f'supervisorctl reload {self.alias}')

    def configure(self):
        config = self._render_config(
            'blueprints/supervisor/asgi.conf',
            PROJECT_NAME=self.server.project.project_name,
            PATH_TO_PROJECT=self.server.project.working_dir_path,
            PATH_TO_ENV=self.server.project.env_path,
            PATH_TO_SOCKETS=self.sockets_path,
            USER=self.server.project.user,
            ALIAS=self.alias,
            PROJECT=self.server.project.wsgi_name
        )
        self.server.copy(
            config, f'{self.alias}.conf', '/etc/supervisor/conf.d'
        )

        api.sudo(f'mkdir -p {self.sockets_path}')
        api.sudo(f'chown -R {self.server.project.user}:{self.server.project.user} {self.sockets_path}')
        api.sudo(f'chmod -R 777 {self.sockets_path}')

        api.sudo(f'supervisorctl reread')
        api.sudo(f'supervisorctl update')
