from django.test import override_settings
from kubeportal.models import WebApplication
from kubeportal.tests import AnonymousTestCase
from unittest.mock import patch


class FrontendAnonymous(AnonymousTestCase):
    '''
    Tests for frontend functionality when nobody is logged in.
    '''

    def test_index_view(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    @override_settings(AUTH_AD_DOMAIN='example.com')
    def test_index_view_ad_status_available(self):
        with patch('kubeportal.social.ad.is_available', return_value=True):
            response = self.c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('available', str(response.content))

    @override_settings(AUTH_AD_DOMAIN='example.com')
    def test_index_view_ad_status_unavailable(self):
        with patch('kubeportal.social.ad.is_available', return_value=False):
            response = self.c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('unavailable', str(response.content))

    @override_settings(AUTH_AD_DOMAIN=None)
    def test_index_view_ad_not_given(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no authentication method', str(response.content))

    def test_subauth_view_nonexistent_app(self):
        response = self.c.get('/subauthreq/42/')
        self.assertEqual(response.status_code, 404)

    def test_subauth_view_existent_app(self):
        app1 = WebApplication(name="app1")
        app1.save()
        response = self.c.get('/subauthreq/{}/'.format(app1.pk))
        self.assertEqual(response.status_code, 401)

    def test_django_secret_generation(self):
        with patch('os.path.isfile', return_value=False):
            response = self.c.get('/stats/')
            self.assertEqual(response.status_code, 302)
