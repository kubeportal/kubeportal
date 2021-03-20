import json

import pytest
from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync, minikube_unavailable


@pytest.mark.django_db
def test_deployment_create_denied(api_client_anon):
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/namespaces/default/deployments/')
    assert response.status_code == 401


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_namespace_deployments_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/')
    assert 200 == response.status_code
    response_data = json.loads(response.content)
    assert len(response_data) > 0
    deployments_url = response_data['deployments_url']

    # fetch list of deployments
    response = api_client.get_absolute(deployments_url)
    assert 200 == response.status_code
    response_data = json.loads(response.content)
    assert len(response_data) > 0
    deployment_urls = response_data['deployment_urls']

    # fetch first deployment info
    response = api_client.get_absolute(deployment_urls[0])
    assert 200 == response.status_code
    deployment = json.loads(response.content)
    assert "coredns" in deployment['name']

    # fetch first pod info
    assert len(deployment['pod_urls']) > 0
    response = api_client.get_absolute(deployment['pod_urls'][0])
    assert 200 == response.status_code
    pod = json.loads(response.content)
    assert "coredns" in pod['name']


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_get_illegal_deployment(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    default_namespace = KubernetesNamespace.objects.get(name="default")

    deployment = api.apps_v1.read_namespaced_deployment('coredns', 'kube-system')

    admin_user.service_account = default_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.namespace}_{deployment.metadata.name}/')
    assert 404 == response.status_code

    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.namespace}_{deployment.metadata.name}/')
    assert 200 == response.status_code


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_deployment(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")

    deployment = api.apps_v1.read_namespaced_deployment('coredns', 'kube-system')

    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.namespace}_{deployment.metadata.name}/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert 'puid' in data.keys()
    assert 'name' in data.keys()
    assert 'creation_timestamp' in data.keys()
    assert 'replicas' in data.keys()
    assert 'pod_urls' in data.keys()
    assert 'namespace_url' in data.keys()


def test_user_deployments_list_no_k8s(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/default/deployments/')
    assert 404 == response.status_code


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_user_deployments_create(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    old_count = len(api.get_namespaced_deployments("kube-system"))
    try:
        response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/kube-system/deployments/',
                                   {'name': 'test-deployment',
                                    'replicas': 1,
                                    'match_labels': [
                                        {'key': 'app', 'value': 'webapp'},
                                    ],
                                    'pod_template': {
                                        'name': 'webapp',
                                        'labels': [
                                            {'key': 'app', 'value': 'webapp'},
                                        ],
                                        'containers': [{
                                            'name': 'busybox',
                                            'image': 'busybox'
                                        }, ]
                                    }})
        assert 201 == response.status_code
        new_count = len(api.get_namespaced_deployments("kube-system"))
        assert old_count + 1 == new_count
    finally:
        api.apps_v1.delete_namespaced_deployment(name="test-deployment", namespace="kube-system")


def test_user_deployments_create_wrong_ns(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/xyz/deployments/',
                               {'name': 'test-deployment',
                                'replicas': 1,
                                'matchLabels': [
                                    {'key': 'app', 'value': 'webapp'},
                                ],
                                'template': {
                                    'name': 'webapp',
                                    'labels': [
                                        {'key': 'app', 'value': 'webapp'},
                                    ],
                                    'containers': [{
                                        'name': 'busybox',
                                        'image': 'busybox'
                                    }, ]
                                }})
    assert 404 == response.status_code