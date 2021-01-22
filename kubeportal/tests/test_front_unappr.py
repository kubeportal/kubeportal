from django.urls import reverse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedInTestCase
from unittest.mock import patch


class FrontendLoggedInNotApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is NOT approved for cluster access.
    '''

    def test_index_view(self):
        # User is already logged in, expecting welcome redirect
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_welcome_view(self):
        response = self.client.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_config_view(self):
        response = self.client.get(reverse('config'))
        self.assertEqual(response.status_code, 200)

    def test_config_download_view(self):
        response = self.client.get(reverse('config_download'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_root_redirect_with_next_param(self):
        response = self.client.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_root_redirect_with_rd_param(self):
        response = self.client.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_acess_request_view(self):
        response = self.client.post('/access/request/', {'selected-administrator' : self.admin.username })
        self.assertRedirects(response, '/config/')

    def test_acess_request_view_mail_broken(self):
        with patch('kubeportal.models.User.send_access_request', return_value=False):
            response = self.client.post('/access/request/', {'selected-administrator' : self.admin.username })
            self.assertRedirects(response, '/config/')
