from django.conf import settings

from kubeportal.k8s import kubernetes_api as api


def test_serviceaccount(api_client, admin_group, admin_user_with_k8s_system):
    uid = admin_user_with_k8s_system.service_account.uid
    response = api_client.get(f'/api/{settings.API_VERSION}/serviceaccounts/{uid}/')
    assert response.status_code == 200
    data = response.json()
    assert 'uid' in data.keys()
    assert 'name' in data.keys()
    assert data['namespace'].startswith('http://testserver')


def test_serviceaccount_no_permission(api_client, admin_user_with_k8s_system):
    for item in api.get_service_accounts():
        if item.metadata.namespace == 'default' and item.metadata.name == 'default':
            uid = item.metadata.uid
            response = api_client.get(f'/api/{settings.API_VERSION}/serviceaccounts/{uid}/')
            assert response.status_code == 404
            return
    assert False


def test_serviceaccount_illegal(api_client, admin_user_with_k8s_system):
    response = api_client.get(f'/api/{settings.API_VERSION}/serviceaccounts/blibblub/')
    assert response.status_code == 404