import os
import kubeportal.k8s.kubernetes_api as k8s_api
from kubeportal.k8s import k8s_sync
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


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
