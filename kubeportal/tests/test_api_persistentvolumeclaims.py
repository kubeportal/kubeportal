import json
import pytest
from urllib.parse import urlparse

from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync, minikube_unavailable, apply_k8s_yml
from kubeportal.tests.test_api import BASE_DIR


@pytest.mark.django_db
def test_pvcs_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/namespaces/default/persistentvolumeclaims/')
    assert response.status_code == 401

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_pvc_list(api_client, admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/pvc1.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    from urllib.parse import urlparse
    pvcs_url = urlparse(data['persistentvolumeclaims_url'])

    response = api_client.get(pvcs_url.path)
    assert 200 == response.status_code
    data = json.loads(response.content)
    pvc_url = urlparse(data['persistentvolumeclaim_urls'][0])

    response = api_client.get(pvc_url.path)
    assert 200 == response.status_code
    data = json.loads(response.content)

    assert "foo-pvc" == data['name']
