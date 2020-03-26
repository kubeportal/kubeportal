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


class BaseTestCase(TestCase):
    def setUp(self):
        self.c = client.Client()

    def _create_user(name):
        User = get_user_model()
        u = User(**admin_data)
        u.save()
        return u



class AnonymousTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

class AdminLoggedOutTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self._create_user()


class AdminLoggedInTestCase(AdminLoggedOutTestCase):
    def login_admin(self):
        self.c.login(username=admin_data['username'],
                     password=admin_clear_password)

    def setUp(self):
        super().setUp()
        self.login_admin()

