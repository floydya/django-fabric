from fabric import api

from .base import Service


__all__ = (
    'ProxyService',
)


class ProxyService(Service):
    name = 'nginx'
    type = 'proxy'
    is_global_service = True

    def soft_restart(self):
        api.sudo('supervisorctl restart nginx')

    def remove(self):
        api.sudo('apt-get remove nginx nginx-common')

    def purge(self):
        api.sudo('apt-get purge --auto-remove nginx nginx-common')

    def configure(self):

        self.server.copy(
            self._render_config(
                'blueprints/supervisor/nginx.conf', ALIAS=self.alias
            ),
            f'nginx.conf',
            '/etc/supervisor/conf.d'
        )

        self.server.enable_service(self.alias)

        has_asgi = hasattr(self.server, 'asgi')
        service_type = 'uwsgi' if hasattr(self.server, 'uwsgi') else 'gunicorn'

        conf = self._render_config(
            'blueprints/conf/server_nginx',
            PROJECT_NAME=self.server.uwsgi.alias,
            DJANGO_SOCKETS_PATH=f'/run/{self.server.project.alias}',
            PATH_TO_PROJECT_ROOT=self.server.project.working_dir_path,
            PORT=self.server.project.project_port,
            HAS_ASGI=has_asgi,
            WEB_SERVICE=service_type,
            ASGI_SOCKET=self.server.asgi.sockets_path if has_asgi else None,
            ASGI_BASE_URL=self.server.asgi.base_url if has_asgi else None,
        )
        alias = self.server._aliased_name('nginx')

        with api.settings(warn_only=True):
            api.sudo(f'rm /etc/nginx/sites-enabled/{alias}')

        # Remove default nginx config.
        with api.settings(warn_only=True):
            api.sudo(f'rm /etc/nginx/sites-enabled/default')

        self.server.copy(
            conf,
            alias,
            '/etc/nginx/sites-available'
        )

        with api.settings(warn_only=True):
            api.sudo(
                f'ln -s '
                f'/etc/nginx/sites-available/{alias} '
                '/etc/nginx/sites-enabled/'
            )
