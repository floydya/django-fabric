import hashlib

from fabric import api, contrib
from .base import Service


__all__ = (
    'DatabaseService',
)


class DatabaseService(Service):
    """
    Service for database. Postgresql with postgis is implemented here
    """
    name = 'postgresql'
    type = 'database'
    postgis = False

    db_user = 'db'
    db_name = 'db'
    is_global_service = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db_user = self.db_name = self.server._aliased_name('db')
        self.db_password = hashlib.sha256(f'{self.db_name}'.encode()
        ).hexdigest()

    def install(self):
        api.sudo('sudo apt-get install -y postgresql postgresql-contrib')

        if self.postgis:
            self.install_postgis()

    def install_postgis(self):
        """
        Installs postgis extension.
        """
        api.sudo('sudo apt-get install -y postgresql-9.5-postgis-scripts')
        api.sudo('add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update')
        api.sudo('apt-get install -y gdal-bin')

    def shell(self, command: str):
        """
        Executes psql command.

        Args:
            command (str): Command to execute in psql shell.
        """
        api.run(f'sudo -u postgres psql -c "{command}"')

    def shell_if(self, copndition: str, then: str):
        """
        Executes psql command only on valid conditions.

        Args:
            copndition (str): Condition to execute `then` command.
            then (str): Command to execute on valid conditions.
        """
        api.run(
            f'sudo -u postgres psql -tc {copndition} | grep -q 1 || sudo -u postgres psql -c {then};'
        )

    def shell_db(self, command: str):
        """
        Executes psql command directly on database.

        Args:
            db_name (str): Database name.
            command (str): Command to execute.
        """
        api.run(f'sudo -u postgres psql -d {self.db_name} -c "{command}"')

    def create_db(self):
        """
        Creates database.

        Args:
            name (str): Database name.
            user (str): Database user name.
            password (str): User password
        """
        with api.settings(warn_only=True):
            self.shell(f'drop database {self.db_name}')
            self.shell(f'drop user {self.db_name}')

        self.shell_if(
            f'"SELECT 1 FROM pg_roles WHERE rolname=\'{self.db_user}\'"',
            f'"CREATE USER {self.db_user} WITH PASSWORD \'{self.db_password}\'"',
        )

        create_db_command = (
            f'"CREATE DATABASE {self.db_name} '
            f'ENCODING \'UTF-8\' '
            f'LC_COLLATE \'en_US.UTF-8\' '
            f'LC_CTYPE \'en_US.UTF-8\' '
            f'OWNER {self.db_user} '
            'TEMPLATE template0"'
        )

        self.shell_if(
            f'"SELECT 1 FROM pg_database WHERE datname = \'{self.db_name}\'"',
            create_db_command
        )

        self.shell(
            f'GRANT ALL PRIVILEGES ON DATABASE "{self.db_name}" to {self.db_user}'
        )

        # Create postgis if you need it
        if self.postgis:
            with api.settings(warn_only=True):
                self.shell_db(self.db_name, 'CREATE EXTENSION postgis;')

        contrib.files.append(
            '/etc/postgresql/10/main/pg_hba.conf',
            'local   all         all                           md5'
        )
        self.soft_restart()

    def configure(self):
        self.server.copy(
            self._render_config(
                'blueprints/supervisor/postgres.conf', ALIAS=self.alias
            ), 
            f'postgres.conf', 
            '/etc/supervisor/conf.d'
        )

        self.server.enable_service(self.alias)
