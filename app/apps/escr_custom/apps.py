from django.apps import AppConfig


class EscrCustomConfig(AppConfig):
    """
    This deployment's additions to eScriptorium, kept out of upstream's code:
    our settings module (settings.py) adds this app and our URLs on top of
    upstream's, and everything else hooks in from here.
    """
    name = 'escr_custom'
    verbose_name = 'eScriptorium customisations'

    def ready(self):
        from .training import hooks
        hooks.install()
