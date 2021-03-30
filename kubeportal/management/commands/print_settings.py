from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **option):
        print("Overview of most relevant settings:")
        print(f"  KubePortal version: {settings.VERSION}")
        print(f"  Developer mode: {settings.DEBUG}")
        print(f"  Allowed target URLs: {settings.ALLOWED_URLS}")
        print(f"  Allowed target hosts: {settings.ALLOWED_HOSTS}")
        print(f"  Database Engine: {settings.DATABASES['default']['ENGINE']}")
        print(f"  eMail host: {settings.EMAIL_HOST}")
        print(f"  K8S API Server: {settings.API_SERVER_EXTERNAL}")
        print(f"  K8S Ingress TLS Issuer: {settings.INGRESS_TLS_ISSUER}")

