import pytest
from django.urls import reverse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication


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


def _prepare_subauth_test(user_in_group1, user_in_group2, app_in_group1, app_in_group2, app_enabled, admin_user):
    group1 = PortalGroup()
    group1.save()
    if user_in_group1:
        admin_user.portal_groups.add(group1)
        admin_user.save()

    group2 = PortalGroup()
    group2.save()
    if user_in_group2:
        admin_user.portal_groups.add(group2)
        admin_user.save()

    app1 = WebApplication(name="app1", can_subauth=app_enabled)
    app1.save()

    if app_in_group1:
        group1.can_web_applications.add(app1)
        group1.save()

    if app_in_group2:
        group2.can_web_applications.add(app1)
        group2.save()

    return app1.pk


@pytest.mark.parametrize("case, expected",[
                         # Constellations for group membership of user and app
                         # The expected result value assumes that the app is enabled
                         ((True, True, False, False), 401),
                         ((True, True, True, False), 200),
                         ((True, True, False, True), 200),
                         ((True, True, True, True), 200),
                         # User is in one of the) groups
                         ((True, False, False, False), 401),
                         ((True, False, True, False), 200),
                         ((True, False, False, True), 401),
                         ((True, False, True, True), 200),
                         # User is in none of the) groups
                         ((False, False, False, False), 401),
                         ((False, False, True, False), 401),
                         ((False, False, False, True), 401),
                         ((False, False, True, True), 401)])
def test_subauth_cases(case, expected, settings, admin_user_with_k8s, admin_client):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    app_pk = _prepare_subauth_test(*case, True, admin_user_with_k8s)
    response = admin_client.get('/subauthreq/{}/'.format(app_pk))
    assert expected == response.status_code

    # When the app is disabled, sub-auth should never succeed
    app_pk = _prepare_subauth_test(*case, False, admin_user_with_k8s)
    response = admin_client.get('/subauthreq/{}/'.format(app_pk))
    assert 401 == response.status_code

