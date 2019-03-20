from .default import *

# By default should be only localhost
ALLOWED_HOSTS = ['{{ ALLOWED_HOSTS }}']

TEMPLATES[0]['OPTIONS']['bytecode_cache']['enabled'] = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / "../logfile.log",
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'logfile']
    },
}


# Uncomment if you want to
# Session is stored in Redis cache
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# SESSION_CACHE_ALIAS = "default"

# ROSETTA CACHE
# ROSETTA_CACHE_NAME = 'default'
# ROSETTA_STORAGE_CLASS = 'rosetta.storage.CacheRosettaStorage'


# Celery settings
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'



# HTTPS settings. Uncomment if you have configured ssl

# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True


# Todo: delete
TWILIO_API_KEY = 'asdasd'