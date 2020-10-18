from django.apps import AppConfig
from django.conf import settings


class KubePortalConfig(AppConfig):
    name = "kubeportal"
    def ready(self):
        # register signals handlers
        import kubeportal.signals
        # print settings overview
        print("Overview of most relevant settings:")
        print(f"  Allowed target URLs: {settings.ALLOWED_URLS}")
        print(f"  Allowed target hosts: {settings.ALLOWED_HOSTS}")


