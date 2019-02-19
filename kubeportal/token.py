"""Implementation of Bearer tokens"""
import hashlib
import base64
from django.conf import settings
import cryptography.fernet
__all__ = ['FernetToken', 'InvalidToken']


class InvalidToken(Exception):
    pass


class FernetToken:
    '''Implementation of Fernet tokens for Kubernetes.

    This implementation uses the Django SECRET_KEY to encrypt
    a Kubernetes username into a Bearer token.'''

    def __init__(self, secret=None):
        '''Initialize the token generator.
        secret (if given) must be 32 bytes. Default is Django's SECRET_KEY'''
        if secret is None:
            keybytes = settings.SECRET_KEY.encode('utf-8')
            secret = hashlib.sha256(keybytes).digest()
        secret = base64.encodebytes(secret)
        self.fernet = cryptography.fernet.Fernet(secret)

    def username_to_token(self, username):
        '''Convert a username string to URL-safe base64 string.'''
        token = self.fernet.encrypt(username.encode('utf-8'))
        return base64.urlsafe_b64encode(token).decode('ascii')

    def token_to_username(self, token):
        '''Validate string token.
        Return username if valid, else raise InvalidToken.'''
        try:
            token = base64.urlsafe_b64decode(token.encode('ascii'))
            return self.fernet.decrypt(token).decode('utf-8')
        except Exception:
            raise InvalidToken from None

    def extract_timestamp(self, token):
        token = base64.urlsafe_b64decode(token.encode('ascii'))
        return self.fernet.extract_timestamp(token)
