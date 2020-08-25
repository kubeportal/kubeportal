from django.urls import reverse
from kubeportal.models import PortalGroup
from kubeportal.models import WebApplication
from kubeportal.tests import AdminLoggedInTestCase
from unittest.mock import patch


class FrontendLoggedInNotApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is NOT approved for cluster access.
    '''

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
        group1 = PortalGroup()
        group1.save()
        self.admin.portal_groups.add(group1)

        app1 = WebApplication(name="app1", can_subauth=True)
        app1.save()

        response = self.c.get('/subauthreq/{}/'.format(app1.pk))

        self.assertEqual(response.status_code, 401)

    def test_acess_request_view(self):
        response = self.c.get('/access/request/')
        self.assertRedirects(response, '/welcome/')

    def test_acess_request_view_mail_broken(self):
        with patch('kubeportal.models.User.send_access_request', return_value=False):
            response = self.c.get('/access/request/')
            self.assertRedirects(response, '/welcome/')
