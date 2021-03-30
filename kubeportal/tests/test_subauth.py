"""
Tests for the sub-authentication feature of the portal.
"""

import pytest

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests.helpers import create_group
from kubeportal.views import SubAuthRequestView
from kubeportal.tests.helpers import minikube_unavailable


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
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
def test_subauth_k8s_user(case, expected, admin_user_with_k8s, admin_client):

    user_in_group1, user_in_group2, app_in_group1, app_in_group2, app_can_subauth = case

    webapp = WebApplication(name="Test Web App", can_subauth=app_can_subauth)
    webapp.save()
    create_group(admin_user_with_k8s if user_in_group1 else None,
                 webapp if app_in_group1 else None)
    create_group(admin_user_with_k8s if user_in_group2 else None,
                 webapp if app_in_group2 else None)

    response = admin_client.get(f'/subauthreq/{webapp.pk}/')

    assert response.status_code == expected


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
@pytest.mark.django_db
@pytest.mark.skip(reason="Subauth caching disabled, since broken")
def test_subauth_caching(admin_user_with_k8s, admin_client, mocker):

    spy = mocker.spy(SubAuthRequestView, 'get')

    # Create new user group, add admin
    group1 = PortalGroup()
    group1.save()
    admin_user_with_k8s.portal_groups.add(group1)

    # Create new web application
    app1 = WebApplication(name="app1", can_subauth=True)
    app1.save()
    webapp = app1.pk

    # allow web application for group
    group1.can_web_applications.add(app1)

    # Second call should be answered from cache
    response = admin_client.get('/subauthreq/{}/'.format(webapp))
    assert response.status_code == 200
    response = admin_client.get('/subauthreq/{}/'.format(webapp))
    assert response.status_code == 200
    spy.assert_called_once()

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
