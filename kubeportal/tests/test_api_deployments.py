import json

import pytest
from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync


@pytest.mark.django_db
def test_deployments_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/namespaces/default/deployments/')
    assert response.status_code == 401


def test_namespace_deployments_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/foobar/deployments/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/deployments/')
    assert 200 == response.status_code
    deployments = json.loads(response.content)
    assert len(deployments) > 0

    # fetch first deployment info
    response = api_client.get_absolute(deployments[0])
    assert 200 == response.status_code
    deployment = json.loads(response.content)
    assert "coredns" in deployment['name']

    # fetch first pod info
    assert len(deployment['pods']) > 0
    response = api_client.get_absolute(deployment['pods'][0])
    assert 200 == response.status_code
    pod = json.loads(response.content)
    assert "coredns" in pod['name']


def test_get_illegal_deployment(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    default_namespace = KubernetesNamespace.objects.get(name="default")

    deployment = api.apps_v1.read_namespaced_deployment('coredns', 'kube-system')

    admin_user.service_account = default_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.uid}/')
    assert 404 == response.status_code

    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.uid}/')
    assert 200 == response.status_code


def test_deployment(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")

    deployment = api.apps_v1.read_namespaced_deployment('coredns', 'kube-system')

    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/{deployment.metadata.uid}/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert 'uid' in data.keys()
    assert 'name' in data.keys()
    assert 'replicas' in data.keys()
    assert 'pods' in data.keys()


def test_user_deployments_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/deployments/')
    assert 404 == response.status_code


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