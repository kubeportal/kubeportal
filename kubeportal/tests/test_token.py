from django.test import TestCase
from kubeportal.token import FernetToken


class FernetTokenTest(TestCase):
    def test_roundtrip(self):
        username = 'kubeportal'
        fernet = FernetToken()
        token = fernet.username_to_token(username)
        username2 = fernet.token_to_username(token)
        self.assertEqual(username2, username)
