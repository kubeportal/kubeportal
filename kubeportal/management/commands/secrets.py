import os
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key
import kubeportal

SECRETS_TEMPLATE = """\
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '{}'
"""


class Command(BaseCommand):
    '''Generate secrets.py if it does not exist'''

    def handle(self, *args, **option):
        filename = os.path.join(kubeportal.__path__[0], 'secrets.py')
        if os.path.exists(filename):
            return
        secret_key = get_random_secret_key()
        with open(filename, 'w') as f:
            f.write(SECRETS_TEMPLATE.format(secret_key))
