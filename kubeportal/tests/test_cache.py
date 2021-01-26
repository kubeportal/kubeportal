import pytest
from django.http import HttpResponse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.views import SubAuthRequestView


@pytest.mark.django_db
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
