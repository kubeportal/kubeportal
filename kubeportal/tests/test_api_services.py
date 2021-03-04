import json

from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync


def test_services_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/namespaces/default/services/')
    assert response.status_code == 401


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


def test_user_services_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/xyz/services/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/services/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "kube-dns" == data[0]['name']
    assert "ClusterIP" == data[0]['type']
    assert 53 == data[0]['ports'][0]['port']
    assert 53 == data[0]['ports'][1]['port']
    assert 'k8s-app' == data[0]['selector'][0]['key']