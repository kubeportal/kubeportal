from django.test import TestCase, client
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model


class AnonTestCase(TestCase):
    def setUp(self):
        self.c = client.Client()

    def index_view(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def admin_index_view(self):
        response = self.c.get('/admin')
        self.assertEqual(response.status_code, 200)
        response = self.c.get('/admin/')
        self.assertEqual(response.status_code, 200)


class LoggedInTestCase(TestCase):
    admin_clear_password = 'adminäö&%/1`'

    admin_data = {
        'username': 'adminäö&%/1`',
        'email': 'adminäö&%/1`@example.com',
        'password': make_password(admin_clear_password),
        'is_staff': True,
        'is_superuser': True
    }

    def setUp(self):
        self.c = client.Client()
        User = get_user_model()
        self.admin = User(**self.admin_data)
        self.admin.save()

    def login_admin(self):
        self.c.login(username=self.admin_data['username'],
                     password=self.admin_clear_password)

    def test_index_view(self):
        self.login_admin()
        # User is already logged in, expecting welcome redirect
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)

    def test_welcome_view(self):
        self.login_admin()
        response = self.c.get('/welcome')
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.login_admin()
        # User is already logged in, expecting redirect
        response = self.c.get('/logout')
        self.assertEqual(response.status_code, 302)


