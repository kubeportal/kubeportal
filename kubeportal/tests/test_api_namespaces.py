from django.conf import settings
import pytest
from kubeportal.tests.helpers import minikube_unavailable


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_namespace(api_client, admin_group, admin_user_with_k8s_system):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/kube-system/')
    assert response.status_code == 200

    data = response.json()
    assert data['name'] == 'kube-system'


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_namespace_no_permission(api_client, admin_user_with_k8s_system):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/')
    assert response.status_code == 404


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_namespace_illegal(api_client, admin_user_with_k8s_system):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/blub/')
    assert response.status_code == 404