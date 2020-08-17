from django.apps import AppConfig


class KubePortalConfig(AppConfig):
    name = "kubeportal"
    def ready(self):
        # register signals handlers
        import kubeportal.signals
