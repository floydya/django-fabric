from .base import Service


__all__ = (
    'CacheService',
)


class CacheService(Service):
    name = 'redis-server'
    type = 'cache'
    is_global_service = True

    def configure(self):
        self.server.copy(
            self._render_config(
                'blueprints/supervisor/redis.conf', 
                ALIAS=self.alias
            ),
            f'redis.conf', 
            '/etc/supervisor/conf.d'
        )
        self.server.copy(
            self._render_config('blueprints/conf/redis.conf'), 
            'redis.conf', 
            '/etc/redis'
        )

        self.server.enable_service(self.alias)
