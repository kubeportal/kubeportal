from datetime import timedelta
from time import sleep

import pytest

from django.conf import settings as django_settings
from rest_framework import authtoken

API_VERSION = django_settings.API_VERSION


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
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert str(admin_user.pk) in data['user_url']
    assert data['user_url'].startswith("http")
    assert data['news_url'].startswith("http")
    assert data['infos_url'].startswith("http")
    assert data['user_approval_url'].startswith("http")


@pytest.mark.django_db
def test_api_wrong_login(api_client_anon):
    response = api_client_anon.post(f'/api/{API_VERSION}/login/',
                                    {'username': 'username', 'password': 'blabla'})
    assert response.status_code == 400


def test_js_api_bearer_auth(api_client):
    """
    Disable the cookie-based authentication and test the bearer
    auth with the token returned.
    """
    # Simulate JS code calling, add Bearer token
    headers = {'Origin': 'http://testserver', 'Authorization': f'Bearer {api_client.jwt}'}
    response = api_client.get(f'/api/{API_VERSION}/infos/portal_version/', headers=headers)
    assert response.status_code == 200


def test_options_preflight_without_auth(api_client_anon, admin_user, admin_group):
    test_path = [(f'/api/{API_VERSION}/', 'GET'),
                 (f'/api/{API_VERSION}/users/{admin_user.pk}', 'GET'),
                 (f'/api/{API_VERSION}/users/{admin_user.pk}', 'PATCH'),
                 (f'/api/{API_VERSION}/groups/{admin_group.pk}', 'GET'),
                 (f'/api/{API_VERSION}/infos/k8s_apiserver', 'GET'),
                 (f'/api/{API_VERSION}/login/', 'POST'),
                 ]
    for path, request_method in test_path:
        response = api_client_anon.options(path)
        assert 200 == response.status_code, f"Unexpected status code {response.status_code} for {request_method} to path {path}, expected 200"


@pytest.mark.django_db
def test_invalid_google_login(api_client_anon, settings):
    """
    We have no valid OAuth credentials when running the test suite, but at least
    we can check that no crash happens when using this API call with fake data.
    """
    settings.SOCIALACCOUNT_PROVIDERS={'google': {
        'APP': {
            'secret': '123',
            'client_id': '456'
        },
        'SCOPE': ['profile', 'email'],
    }}
    response = api_client_anon.post(f'/api/{API_VERSION}/login_google/',
                                    {'access_token': 'foo', 'code': 'bar'})
    assert response.status_code == 400


def test_cors_single_origin(api_client, settings):
    settings.ALLOWED_URLS=['http://testserver', ]
    headers = {'Origin': 'http://testserver'}
    relative_urls = [f'/api/{API_VERSION}/login/', f'/api/{API_VERSION}/cluster/portal_version/']
    for url in relative_urls:
        response = api_client.get(url, headers=headers)
        assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'
        assert response.headers['Access-Control-Allow-Credentials'] == 'true'


def test_cors_multiple_allowed(api_client, settings):
    settings.ALLOWED_URLS=['http://testserver', 'https://example.org:8000']
    headers = {'Origin': 'http://testserver'}
    response = api_client.get(f'/api/{API_VERSION}/cluster/portal_version/', headers=headers)
    assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'


def test_logout(api_client, admin_user):
    response = api_client.post(f'/api/{API_VERSION}/logout/')
    assert response.status_code == 200


def test_token_refresh(api_client, admin_user):
    """
    The original attempt was to write this test based on a 1-second
    token lifetime, configured as Django settings override. This
    lead to a strange bug were the test was executable alone, but not
    as part of the suite. We suspect some kind of timezone-settings-messup
    here, since the expiration check inside dj_rest_auth broke in this case
    due to "current_time" being shifted by one hour.

    We therefore skip the timeout check here, and concentrate on the refresdh logic only.
    """
    old_jwt = api_client.jwt
    # try verify endpoint
    response = api_client.post(f"/api/{API_VERSION}/token/verify/", {'token': api_client.jwt })
    assert response.status_code == 200
    # try to refresh with the wrong token
    response = api_client.post(f"/api/{API_VERSION}/token/refresh/", {'refresh': api_client.jwt })
    assert response.status_code == 401
    # try to refresh with the correct token
    response = api_client.post(f"/api/{API_VERSION}/token/refresh/", {'refresh': api_client.refresh })
    assert response.status_code == 200
    data = response.json()
    assert 'access' in data
    new_jwt = data['access']
    assert old_jwt != new_jwt
    # try to use the new token
    api_client.jwt = new_jwt
    response = api_client.post(f"/api/{API_VERSION}/token/verify/", {'token': api_client.jwt })
    assert response.status_code == 200
    response = api_client.get(f"/api/{API_VERSION}/news/")
    assert response.status_code == 200
