from . import AnonymousTestCase, AdminLoggedInTestCase
from django.urls import reverse


class FrontendAnonymous(AnonymousTestCase):

    def test_index_view(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)


class FrontendLoggedInNotApproved(AdminLoggedInTestCase):

    def test_index_view(self):
        # User is already logged in, expecting welcome redirect
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)

    def test_welcome_view(self):
        response = self.c.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_config_view(self):
        response = self.c.get(reverse('config'))
        self.assertEqual(response.status_code, 403)

    def test_config_download_view(self):
        response = self.c.get(reverse('config_download'))
        self.assertEqual(response.status_code, 403)

    def test_stats_view(self):
        response = self.c.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_root_redirect_with_next_param(self):
        response = self.c.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_root_redirect_with_rd_param(self):
        response = self.c.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)

    def test_logout_view(self):
        # User is already logged in, expecting redirect
        response = self.c.get('/logout/')
        self.assertEqual(response.status_code, 302)

    def test_acess_request_view(self):
        response = self.c.get('/access/request/')
        self.assertRedirects(response, '/welcome/')


class Backend(AdminLoggedInTestCase):

    def test_admin_index_view(self):
        response = self.c.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def k8s_sync_error(self):
        response = self.c.get(reverse('admin:sync'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'my message')
        