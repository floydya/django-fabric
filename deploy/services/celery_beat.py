from fabric import api

from .base import Service


__all__ = (
    'CeleryBeatService',
)


class CeleryBeatService(Service):
    name = 'celery_beat'
    type = 'celery_beat'
    is_global_service = False

    def __init__(self, server: 'Server'):
        self.server = server
        self.alias = self.name

    def install(self):
        with self.server.project.source_virtualenv():
            api.run(f'pip install celery')

    def configure(self):
        config = self._render_config(
            'blueprints/supervisor/celery_beat.conf',
            PATH_TO_ENV=self.server.project.env_path,
            PATH_TO_PROJECT_ROOT=self.server.project.working_dir_path,
            USER=self.server.project.user,
            ALIAS=self.alias,
        )

        self.server.copy(
            config,
            f'{self.alias}.conf',
            '/etc/supervisor/conf.d'
        )

        api.sudo(f'supervisorctl reread')
        api.sudo(f'supervisorctl update')
        
