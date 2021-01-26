import pytest
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from oidc_provider.views import userinfo

from kubeportal import security
from kubeportal.tests.helpers import oidc_authenticate, create_oidc_client, create_webapp, create_group, \
    create_oidc_token


def test_login_hook(rf, admin_user, mocker):
    """
    OIDC login hook should be called called when someone
    performs a Login through the OIDC functionalities.
    """
    spy = mocker.spy(security, 'oidc_login_hook')
    with pytest.raises(PermissionDenied):
        oidc_authenticate(create_oidc_client(), rf, admin_user)
    spy.assert_called_once()


def test_multiple_groups_one_allowed(rf, admin_user):
    client = create_oidc_client()

    with pytest.raises(PermissionDenied):
        oidc_authenticate(client, rf, admin_user)

    app = create_webapp(client)
    create_group(member=admin_user, app=app)
    create_group(member=admin_user, app=None)

    response = oidc_authenticate(client, rf, admin_user)
    assert response.status_code == 302


def test_multiple_groups_none_allowed(rf, admin_user):
    client1 = create_oidc_client()
    client2 = create_oidc_client()

    create_group(member=admin_user, app=None)
    create_group(member=admin_user, app=None)

    with pytest.raises(PermissionDenied):
        oidc_authenticate(client1, rf, admin_user)

    with pytest.raises(PermissionDenied):
        oidc_authenticate(client2, rf, admin_user)


def test_token_auth(admin_user, rf):
    url = reverse('oidc_provider:userinfo')
    request = rf.post(url, data={}, content_type='multipart/form-data')
    token = create_oidc_token(create_oidc_client(), admin_user, request)
    request.META['HTTP_AUTHORIZATION'] = 'Bearer {0}'.format(
        token.access_token)
    response = userinfo(request)
    assert response.status_code == 200
