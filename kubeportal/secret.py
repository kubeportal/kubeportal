'''
Generation / retrieval of the value for DJANGO_SECRET_KEY.
'''

import os

from django.core.management.utils import get_random_secret_key


def get_secret_key():
    fpath = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'secret_key.txt'

    if not os.path.isfile(fpath):
        key = get_random_secret_key()
        f = open(fpath, 'w')
        f.write(key)
        f.close()
        return key
    else:
        f = open(fpath, 'r')
        key = f.read()
        f.close()
        return key
