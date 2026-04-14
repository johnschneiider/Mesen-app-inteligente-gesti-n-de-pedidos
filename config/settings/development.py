from .base import *

DEBUG = True

SECRET_KEY = config('SECRET_KEY', default='django-insecure-mesenu-dev-only')

ALLOWED_HOSTS = ['*']

# Keep CSRF origin for ngrok dev tunnel
CSRF_TRUSTED_ORIGINS = [
    'https://unlifelike-greenly-tegan.ngrok-free.dev',
]
