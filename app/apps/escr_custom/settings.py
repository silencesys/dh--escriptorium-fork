"""
Settings for this deployment: upstream's, plus our app and URLs.

Select them with the environment variable

    DJANGO_SETTINGS_MODULE=apps.escr_custom.settings

for every service (web, channelserver, celery workers). Upstream's entry
points only set a default, so nothing in their code changes.
"""
import os

from escriptorium.settings import *  # noqa: F401,F403
from escriptorium.settings import INSTALLED_APPS, KRAKEN_TRAINING_BATCH_SIZE_VGSL

INSTALLED_APPS = [*INSTALLED_APPS, 'escr_custom']

# VGSL recognition trains in batches of 8 (our best results; kraken's default
# is 1). The variable still sizes it otherwise, and wins over
# KRAKEN_TRAINING_BATCH_SIZE, which then only applies to other architectures.
KRAKEN_TRAINING_BATCH_SIZE_VGSL = KRAKEN_TRAINING_BATCH_SIZE_VGSL or 8

# the largest batch size one training may choose (training page, "Custom")
KRAKEN_TRAINING_BATCH_SIZE_MAX = int(os.getenv('KRAKEN_TRAINING_BATCH_SIZE_MAX', 64))
ROOT_URLCONF = 'escr_custom.urls'
