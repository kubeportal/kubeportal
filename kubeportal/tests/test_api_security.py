import pytest
from django.conf import settings
from django.test import override_settings


def test_api_login(api_client_anon, admin_user):
    response = api_client_anon.api_login(admin_user)
    # JWT_AUTH_COOKIE not used
    #
    # self.assertIn('Set-Cookie', response.headers)
    # self.assertIn('kubeportal-auth=', response.headers['Set-Cookie'])
    # from http.cookies import SimpleCookie
    # cookie = SimpleCookie()
    # cookie.load(response.headers['Set-Cookie'])
    # self.assertEqual(cookie['kubeportal-auth']['path'], '/')
    # self.assertEqual(cookie['kubeportal-auth']['samesite'], 'Lax,')
    # self.assertEqual(cookie['kubeportal-auth']['httponly'], True)
    data = response.json()
    assert 3 == len(data)
    assert 'links' in data
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert str(admin_user.pk) in data['links']['user']


@pytest.mark.django_db
def test_api_wrong_login(api_client_anon):
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/login/',
                                    {'username': 'username', 'password': 'blabla'})
    assert response.status_code == 400


def test_js_api_bearer_auth(api_client):
    """
    Disable the cookie-based authentication and test the bearer
    auth with the token returned.
    """
    # Disable auth cookie
    del (api_client.client.cookies['kubeportal-auth'])
    # Simulate JS code calling, add Bearer token
    headers = {'Origin': 'http://testserver', 'Authorization': f'Bearer {api_client.jwt}'}
    response = api_client.get(f'/api/{settings.API_VERSION}/info/portal_version/', headers=headers)
    assert response.status_code == 200


def test_options_preflight_without_auth(api_client_anon, admin_user, admin_group):
    test_path = [(f'/api/{settings.API_VERSION}/', 'GET'),
                 (f'/api/{settings.API_VERSION}/users/{admin_user.pk}', 'GET'),
                 (f'/api/{settings.API_VERSION}/users/{admin_user.pk}', 'PATCH'),
                 (f'/api/{settings.API_VERSION}/groups/{admin_group.pk}', 'GET'),
                 (f'/api/{settings.API_VERSION}/info/k8s_apiserver', 'GET'),
                 (f'/api/{settings.API_VERSION}/login/', 'POST'),
                 ]
    for path, request_method in test_path:
        response = api_client_anon.options(path)
        assert 200 == response.status_code, f"Unexpected status code {response.status_code} for {request_method} to path {path}, expected 200"


@override_settings(SOCIALACCOUNT_PROVIDERS={'google': {
    'APP': {
        'secret': '123',
        'client_id': '456'
    },
    'SCOPE': ['profile', 'email'],
}})
@pytest.mark.django_db
def test_invalid_google_login(api_client_anon):
    """
    We have no valid OAuth credentials when running the test suite, but at least
    we can check that no crash happens when using this API call with fake data.
    """
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/login_google/',
                                    {'access_token': 'foo', 'code': 'bar'})
    assert response.status_code == 400


@override_settings(ALLOWED_URLS=['http://testserver', ])
def test_cors_single_origin(api_client):
    headers = {'Origin': 'http://testserver'}
    relative_urls = [f'/api/{settings.API_VERSION}/login/', f'/api/{settings.API_VERSION}/cluster/portal_version/']
    for url in relative_urls:
        response = api_client.get(url, headers=headers)
        assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'
        assert response.headers['Access-Control-Allow-Credentials'] == 'true'


@override_settings(ALLOWED_URLS=['http://testserver', 'https://example.org:8000'])
def test_cors_multiple_allowed(api_client):
    headers = {'Origin': 'http://testserver'}
    response = api_client.get(f'/api/{settings.API_VERSION}/cluster/portal_version/', headers=headers)
    assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'


def test_logout(api_client, admin_user):
    response = api_client.post(f'/api/{settings.API_VERSION}/logout/')
    assert response.status_code == 200

