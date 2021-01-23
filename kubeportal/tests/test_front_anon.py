from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AnonymousTestCase
from unittest.mock import patch


class FrontendAnonymous(AnonymousTestCase):
    '''
    Tests for frontend functionality when nobody is logged in.
    '''

    def test_index_view(self):
        response = self.client.get('/', follow=True)
        assert response.status_code == 200

    def test_subauth_view_nonexistent_app(self):
        response = self.client.get('/subauthreq/42/')
        assert response.status_code == 404

    def test_subauth_view_existent_app(self):
        app1 = WebApplication(name="app1")
        app1.save()
        response = self.client.get('/subauthreq/{}/'.format(app1.pk))
        assert response.status_code == 401

    def test_django_secret_generation(self):
        with patch('os.path.isfile', return_value=False):
            response = self.client.get('/stats/')
            assert response.status_code == 302
