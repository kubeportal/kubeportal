import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from .helpers import create_group


@pytest.mark.django_db
def test_index_view(client):
    response = client.get('/', follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
def test_subauth_view_nonexistent_app(client):
    response = client.get('/subauthreq/42/')
    assert response.status_code == 404


@pytest.mark.django_db
def test_subauth_view_existent_app(client):
    app1 = WebApplication(name="app1")
    app1.save()
    response = client.get('/subauthreq/{}/'.format(app1.pk))
    assert response.status_code == 401


@pytest.mark.django_db
def test_django_secret_generation(client, mocker):
    mocker.patch('os.path.isfile', return_value=False)
    response = client.get('/stats/')
    assert response.status_code == 302


def test_welcome_view(admin_client):
    response = admin_client.get('/welcome/')
    assert response.status_code == 200


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


def test_acess_request_view(admin_client, admin_user):
    response = admin_client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')


def test_acess_request_view_mail_broken(admin_client, admin_user, mocker):
    mocker.patch('kubeportal.models.User.send_access_request', return_value=False)
    response = admin_client.post('/access/request/', {'selected-administrator': admin_user.username})
    assertRedirects(response, '/config/')


def test_config_view(admin_client):
    response = admin_client.get(reverse('config'))
    assert response.status_code == 200


def test_config_download_view(admin_client):
    response = admin_client.get(reverse('config_download'))
    assert response.status_code == 200


def test_stats_view(admin_client):
    response = admin_client.get('/stats/')
    assert response.status_code == 200


@pytest.mark.parametrize("case, expected", [
    # Constellations for group membership of user and app
    ((True, True, False, False, True), 401),
    ((True, True, True, False, True), 200),
    ((True, True, False, True, True), 200),
    ((True, True, True, True, True), 200),
    ((True, False, False, False, True), 401),
    ((True, False, True, False, True), 200),
    ((True, False, False, True, True), 401),
    ((True, False, True, True, True), 200),
    ((False, False, False, False, True), 401),
    ((False, False, True, False, True), 401),
    ((False, False, False, True, True), 401),
    ((False, False, True, True, True), 401),
    # disabled sub-auth for web app should always lead to 401
    ((True, True, False, False, False), 401),
    ((True, True, True, False, False), 401),
    ((True, True, False, True, False), 401),
    ((True, True, True, True, False), 401),
    ((True, False, False, False, False), 401),
    ((True, False, True, False, False), 401),
    ((True, False, False, True, False), 401),
    ((True, False, True, True, False), 401),
    ((False, False, False, False, False), 401),
    ((False, False, True, False, False), 401),
    ((False, False, False, True, False), 401),
    ((False, False, True, True, False), 401)])
@pytest.mark.django_db(transaction=True)
def test_subauth_k8s_user(case, expected, settings, admin_user_with_k8s, admin_client):
    settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

    user_in_group1, user_in_group2, app_in_group1, app_in_group2, app_can_subauth = case

    webapp = WebApplication(name="Test Web App", can_subauth=app_can_subauth)
    webapp.save()
    create_group(admin_user_with_k8s if user_in_group1 else None, 
                 webapp if app_in_group1 else None)
    create_group(admin_user_with_k8s if user_in_group2 else None, 
                 webapp if app_in_group2 else None)

    response = admin_client.get(f'/subauthreq/{webapp.pk}/')
    assert response.status_code == expected


def contains(response, text):
    return text in str(response.content)


def test_webapp_user_not_in_group(admin_client):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    response = admin_client.get('/welcome/')
    # User is not in a group that has this web app enabled
    assert not contains(response, "http://www.heise.de")


def test_webapp_user_in_group(admin_client, admin_user):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    group = PortalGroup()
    group.save()
    admin_user.portal_groups.add(group)
    response = admin_client.get('/welcome/')
    # User is in group, but this group has the web app not enabled
    assert not contains(response, "http://www.heise.de")

    group.can_web_applications.add(app1)
    response = admin_client.get('/welcome/')
    # User is now in a group that has this web app enabled
    assert contains(response, "http://www.heise.de")
    assert 1 == str(response.content).count("http://www.heise.de")

    app1.link_show = False
    app1.save()
    response = admin_client.get('/welcome/')
    # User is now in a group that has this web app, but disabled
    assert not contains(response, "http://www.heise.de")


def test_webapp_user_in_multiple_groups(admin_client, admin_user):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    group1 = PortalGroup()
    group1.save()
    group1.can_web_applications.add(app1)
    group2 = PortalGroup()
    group2.save()
    group2.can_web_applications.add(app1)
    admin_user.portal_groups.add(group1)
    admin_user.portal_groups.add(group2)
    response = admin_client.get('/welcome/')
    assert contains(response, "http://www.heise.de")
    assert 1 == str(response.content).count("http://www.heise.de")
