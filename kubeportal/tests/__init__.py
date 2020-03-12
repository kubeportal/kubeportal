from django.contrib.auth.hashers import make_password
from django.test import TestCase, client
from django.contrib.auth import get_user_model


admin_clear_password = 'adminäö&%/1`'

admin_data = {
    'username': 'adminäö&%/1`',
    'email': 'adminäö&%/1`@example.com',
    'password': make_password(admin_clear_password),
    'is_staff': True,
    'is_superuser': True
}


class AdminLoggedInTestCase(TestCase):
    def login_admin(self):
        self.c.login(username=admin_data['username'],
                     password=admin_clear_password)

    def setUp(self):
        self.c = client.Client()
        User = get_user_model()
        self.admin = User(**admin_data)
        self.admin.save()
        self.login_admin()


class AnonymousTestCase(TestCase):
    def setUp(self):
        self.c = client.Client()
