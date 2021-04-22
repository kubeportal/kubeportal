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
        if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY is not None and settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET is not None:
            print(f"  Google Auth configured: True ({settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY})")
        else:
            print("  Google Auth configured: False")

