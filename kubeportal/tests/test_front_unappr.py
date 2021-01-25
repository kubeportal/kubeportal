from django.urls import reverse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication

def test_index_view(admin_client):
    # User is already logged in, expecting welcome redirect
    response = admin_client.get('/')
    assert response.status_code == 302

def test_welcome_view(admin_client):
    response = admin_client.get('/welcome/')
    assert response.status_code == 200

def test_config_view(admin_client):
    response = admin_client.get(reverse('config'))
    assert response.status_code == 200

def test_config_download_view(admin_client):
    response = admin_client.get(reverse('config_download'))
    assert response.status_code == 200

def test_stats_view(admin_client):
    response = admin_client.get('/stats/')
    assert response.status_code == 200

def test_root_redirect_with_next_param(admin_client):
    response = admin_client.get('/?next=/config')
    assert response.status_code == 302

def test_root_redirect_with_rd_param(admin_client):
    response = admin_client.get('/?next=/config')
    assert response.status_code == 302

def test_acess_request_view(admin_client):
    response = admin_client.post('/access/request/', {'selected-administrator' : self.admin.username })
    self.assertRedirects(response, '/config/')

def test_acess_request_view_mail_broken(admin_client, mocker):
    with mocker.patch('kubeportal.models.User.send_access_request', return_value=False):
        response = self.client.post('/access/request/', {'selected-administrator' : self.admin.username })
        self.assertRedirects(response, '/config/')
