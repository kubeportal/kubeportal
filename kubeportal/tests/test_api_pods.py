import json

import pytest
from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync


@pytest.mark.django_db
def test_pods_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/pods/')
    assert response.status_code == 401


def test_namespace_pods_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/foobar/pods/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/pods/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert len(data) > 0   # set of hyperlinks to pods
    assert data[0].startswith("http://testserver")


def test_get_pod(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    pod = api.core_v1.read_namespaced_pod('kube-apiserver-minikube', 'kube-system')

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/{pod.metadata.uid}/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert data['name'] == 'kube-apiserver-minikube'
    assert data['containers'][0]['name'] == 'kube-apiserver'


def test_get_illegal_pod(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    default_namespace = KubernetesNamespace.objects.get(name="default")
    admin_user.service_account = default_namespace.service_accounts.all()[0]
    admin_user.save()

    pod = api.core_v1.read_namespaced_pod('kube-apiserver-minikube', 'kube-system')

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/{pod.metadata.uid}/')
    assert 404 == response.status_code


def test_namespace_pods_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/pods/')
    assert 404 == response.status_code