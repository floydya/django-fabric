from fabric import api
from typing import TYPE_CHECKING
import jinja2

from deploy.path import Path

if TYPE_CHECKING:
    from deploy.server import Server


__all__ = (
    'Service'
)


class Service():
    name = ''
    blueprints_path = ''
    type = ''
    is_global_service = True

    def __init__(self, server: 'Server'):
        self.server = server

        if not self.is_global_service:
            self.alias = self.server._aliased_name(self.name)
        else:
            self.alias = self.name

    @property
    def is_installed(self) -> bool:
        with api.settings(warn_only=True):
            if api.sudo(f'find /etc/supervisor/conf.d/ | grep "{self.alias}"'):
                return True

        return False

    def _render_config(self, file_path, **context):
        path = Path(file_path)

        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(path.parents[0].absolute()))
        ).get_template(path.name).render(context)

    def install(self):
        api.sudo(f'apt-get install -y {self.alias}')

    def configure(self):
        return

    def create(self):
        self.install()
        self.configure()
        self.start()

    def status(self):
        api.sudo(f'supervisorctl status {self.alias}')

    def start(self):
        api.sudo(f'supervisorctl start {self.alias}')

    def stop(self):
        api.sudo(f'supervisorctl stop {self.alias}')

    def remove(self):
        api.sudo(f'apt-get remove {self.alias}')

    def purge(self):
        api.sudo(f'apt-get purge --auto-remove {self.alias}')

    def restart(self):
        api.sudo(f'supervisorctl restart {self.alias}')

    def soft_restart(self):
        self.restart()
