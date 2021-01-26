"""
Internal helper functions.
"""

import os
import uuid
import random

from django.utils.http import urlencode
from oidc_provider.lib.utils.token import create_token, create_id_token
from oidc_provider.models import Client, ResponseType
from oidc_provider.views import AuthorizeView

import kubeportal.k8s.kubernetes_api as k8s_api
from kubeportal.k8s import k8s_sync
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from kubernetes import utils as k8s_utils
from kubeportal.k8s import kubernetes_api
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication


def run_minikube_sync():
    """
    Perform synchronization between Minikube and the portal database.
    """
    os.system("(minikube status | grep Running) || minikube start")

    assert k8s_api.is_minikube()

    # prepare valid request object for admin backend page
    factory = RequestFactory()
    request = factory.post(reverse('admin:index'))
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    k8s_sync.sync(request)


def admin_request(rf, admin_user, rel_url):
    """
    Returns a valid HttpRequest object for the Django admin backend.
    """
    url = reverse(rel_url)
    request = rf.get(url)
    request.user = admin_user
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request


def apply_k8s_yml(path):
    """
    Applies a YML file on disk to the Minikube installation.
    """
    try:
        k8s_utils.create_from_yaml(kubernetes_api.api_client, path)
    except k8s_utils.FailToCreateError as e:
        if e.api_exceptions[0].reason == "Conflict":
            pass  # test namespace still exists in Minikube from another run
        else:
            raise e


def create_oidc_client():
    factory = RequestFactory()
    client = Client()
    client.name = "OIDC"
    client.client_id = str(random.randint(1, 999999)).zfill(6)
    client.client_secret = str(random.randint(1, 999999)).zfill(6)
    client.redirect_uris = ['http://example.com/']
    client.require_consent = False
    client.save()
    client.response_types.add(ResponseType.objects.get(value='code'))
    return client


def create_webapp(oidc_client):
    app = WebApplication(name="Test Web App", oidc_client=oidc_client)
    app.save()
    return app


def oidc_authenticate(oidc_client, rf, admin_user):
    data = {
        'client_id': oidc_client.client_id,
        'redirect_uri': oidc_client.default_redirect_uri,
        'response_type': 'code',
        'scope': 'openid email',
        'state': uuid.uuid4().hex,
        'allow': 'Accept',
    }

    query_str = urlencode(data).replace('+', '%20')
    url = reverse('oidc_provider:authorize') + '/?' + query_str
    request = rf.get(url)
    request.user = admin_user
    return AuthorizeView.as_view()(request)


def create_oidc_token(oidc_client, admin_user, request):
    scope = ['openid', 'email']

    token = create_token(
        user=admin_user,
        client=oidc_client,
        scope=scope)

    id_token_dic = create_id_token(
        token=token,
        user=admin_user,
        aud=oidc_client.client_id,
        nonce='abcdefghijk',
        scope=scope,
        request=request
    )

    token.id_token = id_token_dic
    token.save()

    return token


def create_group(member=None, app=None):
    group = PortalGroup(name="Test Group")
    group.save()
    if member:
        group.members.add(member)
    if app:
        group.can_web_applications.add(app)
    group.save()
    return group
