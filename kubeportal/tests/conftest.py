import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.urls import reverse

from .helpers import run_minikube_sync, admin_request
from ..models.kubernetesnamespace import KubernetesNamespace


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
    default_ns = KubernetesNamespace.objects.get(name='default')
    admin_user.service_account = default_ns.service_accounts.get(name='default')
    admin_user.save()
    return admin_user


@pytest.fixture
def admin_index_request(rf, admin_user):
    """
    A PyTest fixture returning a HttpRequest object for the Django backend index page.
    """
    return admin_request(rf, admin_user, 'admin:index')


@pytest.fixture
def admin_cleanup_request(rf, admin_user):
    """
    A PyTest fixture returning a HttpRequest object for the Django backend cleanup page.
    """
    return admin_request(rf, admin_user, 'admin:cleanup')


@pytest.fixture
def second_user(django_user_model):
    """
    A PyTest fixture returning a second user.
    """
    second_user = django_user_model(username="Fred")
    second_user.save()
    return second_user

