import json

import pytest
from django.conf import settings

from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import KubernetesNamespace
from kubeportal.tests.helpers import run_minikube_sync, apply_k8s_yml, minikube_unavailable
from kubeportal.tests.test_api import BASE_DIR

@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_storageclass_list(api_client, admin_user_with_k8s):
    response = api_client.get(f'/api/{settings.API_VERSION}/storageclasses/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "standard" in data["classes"]
