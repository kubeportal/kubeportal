"""
Custom PyTest fixtures for this project.
"""

import pytest
import random
import string
from django.conf import settings
from rest_framework.test import RequestsClient
from django.core.cache import cache

from .helpers import run_minikube_sync, admin_request
from kubeportal.k8s import kubernetes_api as api
from ..models.kubernetesnamespace import KubernetesNamespace
from ..models.portalgroup import PortalGroup


@pytest.fixture(autouse=True)
def run_around_tests():
    """
    A PyTest fixture with activities to happen before and after each test run.
    """
    cache.clear()   # using the settings fixture to change to dummy cache did not work
    yield


@pytest.fixture
def random_namespace_name():
    """
    A PyTest fixture that creates a usable temporary Kubernetes namespace name for testing.
    It is ensured that the namespace is thrown away afterwards.
    """
    random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    yield random_name
    try:
        api.delete_k8s_ns(random_name)
    except:
        pass


@pytest.mark.usefixtures("db")
@pytest.fixture
def minikube_sync():
    """
    A PyTest fixture making sure that the Minikube installation was synced
    to the portal database.
    """
    run_minikube_sync()


@pytest.fixture
def admin_user_with_k8s(admin_user):
    """
    A PyTest fixture returning a valid admin user with K8S access.
    """
    run_minikube_sync()
    ns = KubernetesNamespace.objects.get(name='default')
    admin_user.service_account = ns.service_accounts.get(name='default')
    admin_user.save()
    return admin_user


@pytest.fixture
def admin_user_with_k8s_system(admin_user):
    """
    A PyTest fixture returning a valid admin user with K8S access.
    """
    run_minikube_sync()
    ns = KubernetesNamespace.objects.get(name='kube-system')
    admin_user.service_account = ns.service_accounts.get(name='default')
    admin_user.save()
    return admin_user


@pytest.fixture
def admin_index_request(rf, admin_user):
    """
    A PyTest fixture returning a HttpRequest object for the Django backend index page.
    """
    return admin_request(rf, admin_user, 'admin:index')


@pytest.fixture
def second_user(django_user_model):
    """
    A PyTest fixture returning a second user.
    """
    second_user = django_user_model(username="Fred")
    second_user.save()
    return second_user


@pytest.fixture
def admin_group(admin_user):
    """
    A PyTest fixture returning a portal group that has the admin user as member.
    """
    admin_group = PortalGroup(name="Admins", can_admin=True)
    admin_group.save()
    admin_group.members.add(admin_user)
    admin_group.save()
    return admin_group


class ApiClient:
    def __init__(self):
        self.client = RequestsClient()
        self.csrf = None
        self.jwt = None

    def get(self, relative_url, headers={}):
        return self.get_absolute('http://testserver' + relative_url, headers)

    def get_absolute(self, url, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        return self.client.get(url, headers=headers)

    def patch(self, relative_url, data, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        if self.csrf:
            headers['X-CSRFToken'] = self.csrf
        return self.client.patch('http://testserver' + relative_url,
                                 json=data, headers=headers)

    def post(self, relative_url, data=None, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        if self.csrf:
            headers['X-CSRFToken'] = self.csrf
        return self.client.post('http://testserver' + relative_url,
                                json=data, headers=headers)

    def options(self, relative_url, headers={}):
        return self.client.options('http://testserver' + relative_url, headers=headers)

    def api_login(self, user):
        user.set_password("passwort")
        user.save()

        response = self.post(f'/api/{settings.API_VERSION}/login/',
                             {'username': user.username, 'password': 'passwort'})
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        self.jwt = data['access_token']
        return response


@pytest.fixture
def api_client(admin_user):
    c = ApiClient()
    c.api_login(admin_user)
    return c


@pytest.fixture
def api_client_anon():
    c = ApiClient()
    return c
