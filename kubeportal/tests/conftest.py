import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from .helpers import run_minikube_sync, admin_request

@pytest.mark.usefixtures("db")
@pytest.fixture
def minikube_sync():  
    run_minikube_sync()

@pytest.fixture
def admin_index_request(rf, admin_user):
    return admin_request(rf, admin_user, 'admin:index')

@pytest.fixture
def admin_cleanup_request(rf, admin_user):
    return admin_request(rf, admin_user, 'admin:cleanup')
