"""
Tests for model functions.
"""

import os
import pytest
from kubeportal.models.webapplication import WebApplication
from kubeportal.models.portalgroup import PortalGroup
from .helpers import create_group, apply_k8s_yml
from kubeportal.tests.helpers import minikube_unavailable

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_k8s_namespaces(admin_user_with_k8s):
    assert admin_user_with_k8s.k8s_namespaces()[0].name == "default"

def test_user_inactive_users(admin_user):
    assert admin_user.inactive_users() == []

def test_user_web_applications(admin_user):
    app1 = WebApplication(name="Test Web App 1", link_show=True)
    app1.save()
    app2 = WebApplication(name="Test Web App 2", link_show=False)
    app2.save()

    group = create_group(member=admin_user)
    group.can_web_applications.add(app1)
    group.can_web_applications.add(app2)
    group.save()

    admin_user.portal_groups.add(group)
    admin_user.save()

    assert len(admin_user.web_applications(include_invisible=True)) == 2
    assert len(admin_user.web_applications(include_invisible=False)) == 1

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_pods(admin_user_with_k8s_system):
    assert len(admin_user_with_k8s_system.k8s_pods()) > 0

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_deployments(admin_user_with_k8s_system):
    assert len(admin_user_with_k8s_system.k8s_deployments()) > 0

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_services(admin_user_with_k8s_system):
    assert len(admin_user_with_k8s_system.k8s_services()) > 0

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_ingresses(admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")
    assert len(admin_user_with_k8s.k8s_ingresses()) > 0

def test_user_pods_no_k8s(admin_user):
    assert len(admin_user.k8s_pods()) == 0

def test_user_deployments_no_k8s(admin_user):
    assert len(admin_user.k8s_deployments()) == 0

def test_user_services_no_k8s(admin_user):
    assert len(admin_user.k8s_services()) == 0

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_ingresses_no_k8s(admin_user):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")
    assert len(admin_user.k8s_ingresses()) == 0
