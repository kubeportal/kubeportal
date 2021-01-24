"""
Internal helper functions.
"""


import os
import kubeportal.k8s.kubernetes_api as k8s_api
from kubeportal.k8s import k8s_sync
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from kubernetes import utils as k8s_utils
from kubeportal.k8s import kubernetes_api

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
