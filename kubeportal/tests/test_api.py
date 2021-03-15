"""
Tests for the Kubeportal REST API.

We take the more complicated way here, and implement the API tests
with Python requests. This ensures that we are getting as close as possible
to 'real' API clients, e.g. from JavaScript.

CRSF token and JWT are transported as cookie by default, in Django.
The HTTP verb methods allow to override this and add according headers
with the information. This is intended to support testing JavaScript AJAX calls,
with seem to have trouble accessing the cookies sometimes. Ask @Kat-Hi.
"""

import logging
import os
import pytest
from django.conf import settings

logger = logging.getLogger('KubePortal')

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


@pytest.mark.django_db
def test_api_bootstrap(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/')
    assert response.status_code == 200
    data = response.json()
    assert 2 == len(data)
    assert 'csrf_token' in data
    assert 'links' in data
    # check if given login route makes sense
    # login path response tells us to use something else than GET
    response = api_client_anon.get_absolute(data['links']['login_url'])
    assert response.status_code == 405


