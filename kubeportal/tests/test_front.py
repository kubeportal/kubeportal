"""
Tests for the (classic) portal frontend, assuming that a user is logged in
and that she has an approved cluster access.
"""

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from .helpers import create_group


@pytest.mark.django_db
def test_index_view(client):
    response = client.get('/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_django_secret_generation(client, mocker):
    mocker.patch('os.path.isfile', return_value=False)
    response = client.get('/stats/')
    assert response.status_code == 302


def test_welcome_view(admin_client):
    response = admin_client.get('/welcome/')
    assert response.status_code == 200


def test_index_view_admin(admin_client):
    # User is already logged in, expecting welcome redirect
    response = admin_client.get('/')
    assert response.status_code == 302


def test_welcome_view_admin(admin_client):
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


def test_config_view_admin(admin_client):
    response = admin_client.get(reverse('config'))
    assert response.status_code == 200


def test_config_download_view_admin(admin_client):
    response = admin_client.get(reverse('config_download'))
    assert response.status_code == 200


def test_stats_view_admin(admin_client):
    response = admin_client.get('/stats/')
    assert response.status_code == 200


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
