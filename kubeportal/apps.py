from django.apps import AppConfig
from django.conf import settings


class KubePortalConfig(AppConfig):
    name = "kubeportal"
    def ready(self):
        # register signals handlers
        import kubeportal.signals
