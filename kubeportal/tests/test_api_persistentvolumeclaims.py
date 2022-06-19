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
    try:
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

        pending_count = 0
        pending = True
        while pending:
            pending_count += 1
            if pending_count > 100:
                assert False, "Waiting for pending PVC took too long."
            response = api_client.get(pvc_url.path)
            assert 200 == response.status_code
            data = json.loads(response.content)
            pending = (data['phase'] == 'Pending')

        assert "foo-pvc" == data['name']
        assert "standard" == data['storage_class_name']
        assert data['access_modes']
        assert data['access_modes'][0] == 'ReadWriteOnce'
        assert data['phase'] == 'Bound'
        assert data['size'] == '100Mi'
    finally:
        api.get_portal_core_v1().delete_namespaced_persistent_volume_claim(name="foo-pvc", namespace="default")


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_pvc_create(api_client, admin_user):
    run_minikube_sync()
    namespace = KubernetesNamespace.objects.get(name="default")
    admin_user.service_account = namespace.service_accounts.all()[0]
    admin_user.save()
    pvcs = api.get_namespaced_pvcs("default", admin_user)
    try:
        assert len(pvcs) == 0
        response = api_client.post(f'/api/{settings.API_VERSION}/namespaces/default/persistentvolumeclaims/',
                                   {'name': 'test-pvc',
                                    'access_modes': ['ReadWriteOnce', 'ReadWriteMany'],
                                    'storage_class_name': 'standard',
                                    'size': '10Mi'
                                    })
        assert 201 == response.status_code
        pvcs = api.get_namespaced_pvcs("default", admin_user)
        assert len(pvcs) > 0
    finally:
        api.get_portal_core_v1().delete_namespaced_persistent_volume_claim(name="test-pvc", namespace="default")


@pytest.mark.skipif(minikube_unavailable(), reason="Minikube is unavailable")
def test_empty_pvc_list(api_client, admin_user_with_k8s):
    response = api_client.get(f'/api/{settings.API_VERSION}/namespaces/default/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    from urllib.parse import urlparse
    pvcs_url = urlparse(data['persistentvolumeclaims_url'])

    response = api_client.get(pvcs_url.path)
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert len(data['persistentvolumeclaim_urls']) == 0
