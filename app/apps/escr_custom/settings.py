"""
Settings for this deployment: upstream's, plus our app and URLs.

Select them with the environment variable

    DJANGO_SETTINGS_MODULE=apps.escr_custom.settings

for every service (web, channelserver, celery workers). Upstream's entry
points only set a default, so nothing in their code changes.
"""
from escriptorium.settings import *  # noqa: F401,F403
from escriptorium.settings import INSTALLED_APPS

INSTALLED_APPS = [*INSTALLED_APPS, 'escr_custom']
ROOT_URLCONF = 'escr_custom.urls'
