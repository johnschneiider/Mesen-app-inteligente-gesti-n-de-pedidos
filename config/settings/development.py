from .base import *

DEBUG = True

SECRET_KEY = config('SECRET_KEY', default='django-insecure-mesenu-dev-only')

ALLOWED_HOSTS = ['*']
