import io, os
from typing import Any
from deploy.path import Path

from fabric import api, contrib, operations


__all__ = (
    'Server',
    'FileSystem',
)


class FileSystem():

    def path_exists(self, path: Path) -> bool:
        return contrib.files.exists(path)

    def path_prepared(self, path: Path) -> bool:
        api.sudo(f'rm -rf {path}')
        # if self.path_exists(path):
        #     to_remove = operations.prompt(
        #         f'{path} already exists. Remove it?',
        #         default='Y'
        #     )

        #     if to_remove.lower() == 'y' or not to_remove:
        #         api.sudo(f'rm -rf {path}')
        #     else:
        #         return False

        return True

    def create_directory(self, path: Path, username: str, perms: int=770):
        if not self.path_prepared(path):
            return

        api.sudo(f'mkdir -p {path}')
        self.set_permissions(username, path, perms)

    def copy(self, data: str, name: str, dest: Path):
        file = io.StringIO(str(data))
        file.name = name
        file.filename = name

        api.sudo(f'rm -rf {dest}/{name}')
        api.put(file, f'{dest}/{name}', use_sudo=True)

    def set_permissions(self, username: str, path: Path, perms: int=777):
        api.sudo(f'chmod -R {perms} {path}'.replace('\\', '/'))
        api.sudo(f'chown -R {username}:{username} {path}'.replace('\\', '/'))


class Server(FileSystem):

    def __init__(self, services):
        self.services = services
        self.process_services()

    @property
    def _project_alias(self):
        return os.environ['DEPLOY_PROJECT_ALIAS']

    def _aliased_name(self, name: str):
        return f'{self._project_alias}_{name}'

    def process_services(self):
        self.services = [service(server=self) for service in self.services]
        self._services = {x.name: x for x in self.services}

        for service in self.services:
            setattr(self, service.type, service)

    def create_user(self, username: str):
        with api.settings(warn_only=True):
            result = api.sudo(f'id -u {username}')

            if result.return_code != 1:
                print(f'The user {username} already exists')
            else:
                api.sudo(f'adduser -gecos "" --disabled-password {username}')

    def enable_service(self, name: str):
        api.sudo('systemctl daemon-reload')
        api.sudo(f'systemctl disable {name}.service')
        api.sudo(f'systemctl stop {name}.service')
        api.sudo(f'supervisorctl reread')
        api.sudo(f'supervisorctl update')

    def get_service(self, service_name: str) -> Any:
        return self._services.get(service_name)

    def preconfigure(self):
        api.sudo('locale-gen en_US')
        api.sudo('locale-gen en_US.UTF-8')
        api.sudo('update-locale')

        api.sudo('apt-get update')
        api.sudo('''
            apt-get install -y htop git \
                gettext libtiff5-dev libjpeg8-dev zlib1g-dev \
                libfreetype6-dev liblcms2-dev libwebp-dev libpq-dev \
                build-essential libssl-dev libffi-dev tcl supervisor
        ''')
        # api.sudo('echo "*    soft nofile 1048576\n*    hard nofile 1048576\nroot soft nofile 1048576\nroot hard nofile 1048576" >> /etc/security/limits.conf')
        # api.sudo('echo "session required pam_limits.so" >> /etc/pam.d/common-session')
        # api.sudo('echo "fs.file-max=2097152\nfs.nr_open=1048576" >> /etc/sysctl.conf')
        # api.sudo('echo "net.ipv4.netfilter.ip_conntrack_max=1048576\nnet.nf_conntrack_max=1048576\nnet.core.somaxconn=1048576" >> /etc/sysctl.conf')
        # api.sudo('fallocate -l 4G /swapfile')
        # api.sudo('chmod 600 /swapfile')
        # api.sudo('mkswap /swapfile')
        # api.sudo('swapon /swapfile')
        # api.sudo('echo "vm.swappiness=10\nvm.vfs_cache_pressure=50" >> /etc/sysctl.conf')
        # api.sudo('echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab')

    def install_services(self):
        for service in self.services:
            service.install()
            service.configure()

        for service in self.services:
            service.status()

    def restart_services(self):
        with api.settings(warn_only=True):
            for service in self.services:
                    service.restart()

    def check(self):
        if not self.project.user:
            raise AttributeError(
                'Set up separate project user in '
                '`app/deploy/services/project.py`'
            )

    def install(self):
        self.check()

        self.preconfigure()

        self.install_services()

        self.restart_services()
