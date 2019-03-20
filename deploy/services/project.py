import time
import os
import binascii
from contextlib import contextmanager

from fabric import api, contrib
from deploy.services.base import Service
from deploy.path import Path


__all__ = (
    'ProjectService',
)


class ProjectService(Service):
    """
    Interface to work with on the project on the remote server.
    Handles such things as installing project from repository,
    updating it, etc

    Attributes:
        branch (str): Git branch to pull.
        db_name (str): Database name.
        db_password (str): Database password.
        name (str): Project's service name.
        project_name (str): Project name
        python (str): Python's service name.
        python_version (str): Version of the python.
        repository (str): Repository url.
        server (object): Server instance.
        user (str): System username.
        wsgi_name (str): Name of the WSGI app.
    """
    # System preferences
    # Your project user. Don't call it django. Use your imagination.
    user = ''

    # Project preferences
    _project_name = ''

    # Repository preferences
    # Use ssh connection not https
    repository = ''
    branch = 'master'

    # Python preferences
    python = 'python3.7'
    # Leave version blank for 2.7
    python_version = '3.7'
    # Project ip address/domain name that will be used in ALLOWED_HOSTS
    project_address = '*'
    # Port to work on. If multiple projects on the same server - change it
    project_port = 80

    # Use jsmakemessages?
    JS_MAKE_MESSAGES = False

    # ssh-keygen pass phrase
    pass_phrase = ''

    # Non editable in most cases.
    name = 'gunicorn'  # Name of the WSGI service
    type = 'project'
    wsgi_name = 'app'
    is_global_service = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.project_name = self._project_name.lower()
        self.ssh_path = f'/root/.ssh/{self.server._project_alias}_rsa'

    @property
    def ssh_repository_url(self) -> str:
        user, path = self.repository.split('@')

        return f'{user}@{self.server._project_alias}.{path}'

    @property
    def user_dir_path(self) -> Path:
        return Path(f'/home/{self.user}')

    @property
    def env_path(self) -> Path:
        return self.working_dir_path / '.venv'

    @property
    def root_path(self) -> Path:
        return self.user_dir_path / self.project_name

    @property
    def dir_path(self) -> Path:
        return self.root_path / self._project_name

    @property
    def working_dir_path(self) -> Path:
        return self.dir_path / 'server'

    @property
    def static_path(self) -> Path:
        return self.working_dir_path / 'app' / 'static'

    @property
    def uploads_path(self) -> Path:
        return self.working_dir_path / 'app' / 'uploads'

    @contextmanager
    def source_virtualenv(self):
        with api.prefix(f'source {self.working_dir_path}/.venv/bin/activate'):
            yield

    def install(self):
        self.server.create_user(self.user)
        self.create_user_directory()
        self.create_project_directory()

        self.install_python()

        self.clone()

        self.install_env()
        self.update_firewall()

    def configure(self):
        self.server.database.create_db()

        self.gen_local_settings()
        self.gen_env()
        self.update()
        self.server.set_permissions(self.user, self.root_path, 775)
        self.create_superuser()
        self.disable_git_permissions_checking()

    def update_firewall(self):
        if self.project_port == 80:
            return

        api.run(f'ufw allow {self.project_port}')

    def disable_git_permissions_checking(self):
        api.run(
            f'cd {self.dir_path} && git config core.fileMode false'
        )

    def create_superuser(self):
        with self.source_virtualenv():
            api.sudo(
                f"""
                echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('root', 'admin@admin.com', 'admin12345')" | python {self.working_dir_path}/manage.py shell
                """
            )

    def gen_local_settings(self):
        local_settings = self._render_config(
            'blueprints/project/local.py',
            ALLOWED_HOSTS=self.project_address,
        )

        self.server.copy(
            local_settings,
            'local.py',
            self.working_dir_path / 'app' / 'settings'
        )

    def gen_env(self):
        env_file = self._render_config(
            'blueprints/project/local.env',
            SECRET_KEY=binascii.hexlify(os.urandom(24)).decode(),
            ALLOWED_HOSTS=self.project_address,
            DB_NAME=self.server.database.db_name,
            DB_USER=self.server.database.db_user,
            DB_PASSWORD=self.server.database.db_password,
        )

        self.server.copy(
            env_file,
            '.env',
            self.working_dir_path
        )

    def generate_ssh_config(self):
        api.run('touch ~/.ssh/config')

        contrib.files.append(
            '~/.ssh/config',

            f'Host {self.server._project_alias}.gitlab.com\n'
            '    HostName gitlab.com\n'
            '    PubkeyAuthentication yes\n'
            f'    IdentityFile {self.ssh_path}\n'
            '    IdentitiesOnly yes\n'
            '    User git\n'
        )

    def clone(self):
        print('Installing ssh key for your repository.')
        time.sleep(2)

        if(not self.server.path_exists(self.ssh_path)):
            api.run(f'ssh-keygen -t rsa -b 4096 -f {self.ssh_path} -N "{self.pass_phrase}"')

        api.run(f'cat {self.ssh_path}.pub')
        api.prompt('Press enter when you\'ve installed ssh key to repository')

        if not self.server.path_prepared(self.dir_path):
            return

        self.generate_ssh_config()
        api.run(
            f'ssh-keyscan gitlab.com >> ~/.ssh/known_hosts'
        )
        api.run(
            f'git clone -b {self.branch} {self.ssh_repository_url} {self.dir_path}',
            # user=self.user
        )

    def create_user_directory(self):
        self.server.create_directory(self.user_dir_path, self.user)

    def create_project_directory(self):
        self.server.create_directory(self.root_path, self.user)

    def pull(self):
        api.sudo(f'git -C {self.dir_path} pull origin {self.branch}')

    def update(self):
        self.pull()
        self.install_requirements()
        self.migrate()
        self.makemessages()
        self.collectstatic()

    def install_python(self):
        api.sudo('apt-get update')

        api.sudo(f'apt-get install -y {self.python}')
        api.sudo(f'PYTHON_VERSION="{self.python_version}"')
        api.sudo(f'sudo apt install -y {self.python}-dev')

    def install_env(self):
        if not self.server.path_exists(self.env_path):
            api.sudo('apt-get install -y python3-pip')
            api.sudo('pip3 install pipenv')
            api.sudo(f'export PIPENV_VENV_IN_PROJECT=True && cd {self.working_dir_path} && pipenv --python {self.python_version}')
            # api.sudo('apt-get install python-pip')
            # api.run('pip install virtualenv')
            # api.run(f'virtualenv -p {self.python} {self.env_path}')

    def install_requirements(self):
        with self.source_virtualenv():
            api.run(f'cd {self.working_dir_path} && pipenv install --dev')
            # api.run(f'pip install -r {self.working_dir_path}/requirements.txt')

    def migrate(self):
        with self.source_virtualenv():
            api.run(f'python {self.working_dir_path}/manage.py migrate')

    def makemessages(self):
        with self.source_virtualenv():
            if not self.JS_MAKE_MESSAGES:
                api.run(
                    f'python {self.working_dir_path}/manage.py makemessages '
                    '--all -e py,html,jinja'
                )
            else:
                api.run(
                    f'cd {self.dir_path} && '
                    f'python server/manage.py jsmakemessages -v3 -e jinja,py,html,js,vue -jse js,vue -i node_modules'
                )

        self.server.set_permissions(self.user, self.user_dir_path, 755)

    def collectstatic(self):
        with self.source_virtualenv():
            api.run(
                f'python {self.working_dir_path}/manage.py collectstatic '
                '--noinput'
            )

        self.server.set_permissions(self.user, self.user_dir_path, 755)

    def restart(self):
        api.sudo(f'supervisorctl restart {self.name}')
