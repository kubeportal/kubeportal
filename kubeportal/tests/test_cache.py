from unittest.mock import patch

import pytest
from django.http import HttpResponse

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedInTestCase


@pytest.fixture
def mocked_subauth(mocker):
    mocker.patch('kubeportal.views.SubAuthRequestView.get', return_value=HttpResponse("Mock response"))
    #TODO: Determine number of calls to get()

class CacheUsage(AdminLoggedInTestCase):
    def setUp(self):
        super().setUp()

    @pytest.mark.usefixtures("mocked_subauth")
    def test_subauth_caching(self):
        # Create new user group, add admin
        group1 = PortalGroup()
        group1.save()
        self.admin.portal_groups.add(group1)

        # Create new web application
        app1 = WebApplication(name="app1", can_subauth=True)
        app1.save()
        webapp = app1.pk

        # allow web application for group
        group1.can_web_applications.add(app1)

        # Second call should be answered from cache
        response = self.client.get('/subauthreq/{}/'.format(webapp))
        response = self.client.get('/subauthreq/{}/'.format(webapp))

