import json

import pytest
from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync, minikube_unavailable


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_namespace_pods_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert len(data) > 0
    pods_list = data["pod_urls"]
    assert pods_list[0].startswith("http://testserver")


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_get_pod(api_client, admin_user):
    run_minikube_sync()

    # Minikube system pod names differ, depending on the version
    pods = api.get_namespaced_pods("kube-system")
    test_pod_name = None
    for k8s_pod in pods:
        if "apiserver" in k8s_pod.metadata.name:
            test_pod_name = k8s_pod.metadata.name
            break
    assert test_pod_name

    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    pod = api.core_v1.read_namespaced_pod(test_pod_name, 'kube-system')

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/{pod.metadata.uid}/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert data['name'] == test_pod_name
    assert data['containers'][0]['name'] == 'kube-apiserver'


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_get_illegal_pod(api_client, admin_user):
    run_minikube_sync()

    # Minikube system pod names differ, depending on the version
    pods = api.get_namespaced_pods("kube-system")
    test_pod_name = None
    for k8s_pod in pods:
        if "apiserver" in k8s_pod.metadata.name:
            test_pod_name = k8s_pod.metadata.name
            break
    assert test_pod_name

    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    default_namespace = KubernetesNamespace.objects.get(name="default")
    admin_user.service_account = default_namespace.service_accounts.all()[0]
    admin_user.save()

    pod = api.core_v1.read_namespaced_pod(test_pod_name, 'kube-system')

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/{pod.metadata.uid}/')
    assert 404 == response.status_code


def test_namespace_pods_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/pods/')
    assert 404 == response.status_code