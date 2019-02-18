import os
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import kubeportal


class Command(BaseCommand):
    '''Propose SECRET_KEY'''

    def handle(self, *args, **option):
        secret_key = get_random_secret_key()
        print("KUBEPORTAL_SECRET_KEY='{}'".format(secret_key))
