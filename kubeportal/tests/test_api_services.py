import json
import pytest

from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync, minikube_unavailable


@pytest.mark.django_db
def test_services_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/namespaces/default/services/')
    assert response.status_code == 401


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_services_create(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    old_count = len(api.get_namespaced_services("kube-system"))
    try:
        response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/kube-system/services/', {
            'name': 'my-service',
            'type': 'NodePort',
            'selector': [{'key': 'app', 'value': 'kubeportal'}, ],
            'ports': [{'port': 8000, 'protocol': 'TCP'}]
        })
        assert 201 == response.status_code
        new_count = len(api.get_namespaced_services("kube-system"))
        assert old_count + 1 == new_count
    finally:
        api.core_v1.delete_namespaced_service(name="my-service", namespace="kube-system")


def test_user_services_create_wrong_ns(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/xyz/services/', {
        'name': 'my-service',
        'type': 'NodePort',
        'selector': [{'key': 'app', 'value': 'kubeportal'}, ],
        'ports': [{'port': 8000, 'protocol': 'TCP'}]
    })
    assert 404 == response.status_code


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_services_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/')
    assert 200 == response.status_code
    data = json.loads(response.content)

    from urllib.parse import urlparse
    services_url = urlparse(data["services_url"])

    response = api_client.get(services_url.path)
    assert 200 == response.status_code
    data = json.loads(response.content)
    service_url = urlparse(data["service_urls"][0])

    response = api_client.get(service_url.path)
    assert 200 == response.status_code
    data = json.loads(response.content)

    assert "kube-dns" == data['name']
    assert "ClusterIP" == data['type']
    assert 53 == data['ports'][0]['port']
    assert 53 == data['ports'][0]['target_port']
    assert 'UDP' == data['ports'][0]['protocol']
    assert 53 == data['ports'][1]['port']
    assert 'k8s-app' == data['selector']['key']