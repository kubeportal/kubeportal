"""
We take the more complicated way here, and implement the API tests
with Python requests. This ensures that we are getting as close as possible
to 'real' API clients, e.g. from JavaScript.

CRSF token and JWT are transported as cookie by default, in Django.
The HTTP verb methods allow to override this and add according headers
with the information. This is intended to support testing JavaScript AJAX calls,
with seem to have trouble accessing the cookies sometimes. Ask @Kat-Hi.
"""

import json
import logging
import os

from django.conf import settings
from django.test import override_settings
from kubernetes import utils as k8s_utils

from kubeportal.api.views import ClusterInfoView
from kubeportal.k8s import kubernetes_api as api
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests.helpers import run_minikube_sync, apply_k8s_yml

logger = logging.getLogger('KubePortal')

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


def test_api_bootstrap(api_client_anon):
    response = api_client_anon.get(f'/api/')
    assert response.status_code == 200
    data = response.json()
    assert 3 == len(data)
    assert 'csrf_token' in data
    assert 'portal_version' in data
    assert 'default_api_version' in data
    default_api_version = data['default_api_version']
    # check if given default API version makes sense
    # login path response tells us to use something else than GET
    response = api_client_anon.get(f'/api/{default_api_version}/login/')
    assert response.status_code == 405


def test_api_login(api_client_anon, admin_user):
    response = api_client_anon.api_login(admin_user)
    # JWT_AUTH_COOKIE not used
    #
    # self.assertIn('Set-Cookie', response.headers)
    # self.assertIn('kubeportal-auth=', response.headers['Set-Cookie'])
    # from http.cookies import SimpleCookie
    # cookie = SimpleCookie()
    # cookie.load(response.headers['Set-Cookie'])
    # self.assertEqual(cookie['kubeportal-auth']['path'], '/')
    # self.assertEqual(cookie['kubeportal-auth']['samesite'], 'Lax,')
    # self.assertEqual(cookie['kubeportal-auth']['httponly'], True)
    data = response.json()
    assert 5 == len(data)
    assert 'group_ids' in data
    assert 'webapp_ids' in data
    assert 'user_id' in data
    assert 'access_token' in data
    assert 'k8s_namespace' in data
    assert data['user_id'] == admin_user.pk


def test_api_wrong_login(api_client_anon):
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/login/', {'username': 'username', 'password': 'blabla'})
    assert response.status_code == 400


def test_js_api_bearer_auth(api_client):
    """
    Disable the cookie-based authentication and test the bearer
    auth with the token returned.
    """
    # Disable auth cookie
    del (api_client.client.cookies['kubeportal-auth'])
    # Simulate JS code calling, add Bearer token
    headers = {'Origin': 'http://testserver', 'Authorization': f'Bearer {api_client.jwt}'}
    response = api_client.get(f'/api/{settings.API_VERSION}/cluster/portal_version/', headers=headers)
    assert response.status_code == 200


def test_cluster_denied(api_client_anon):
    for stat in ClusterInfoView.stats.keys():
        response = api_client_anon.get(f'/api/{settings.API_VERSION}/cluster/{stat}/')
        assert response.status_code == 401


def test_single_webapp_denied(api_client_anon, admin_user, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client_anon.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 401


def test_webapps_denied(api_client_anon, admin_user, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client_anon.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 401


def test_single_group_denied(api_client_anon, admin_user, admin_group):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/groups/{admin_group.pk}/')
    assert response.status_code == 401


def test_groups_denied(api_client_anon):
    group1 = PortalGroup(name="group1")
    group1.save()
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/groups/{group1.pk}/')
    assert response.status_code == 401


def test_pods_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/pods/kube-system/')
    assert response.status_code == 401


def test_ingresses_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/ingresses/default/')
    assert response.status_code == 401


def test_ingresshosts_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/ingresshosts/')
    assert response.status_code == 401


def test_deployments_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/deployments/default/')
    assert response.status_code == 401


def test_services_denied(api_client_anon):
    response = api_client_anon.get(f'/api/{settings.API_VERSION}/services/default/')
    assert response.status_code == 401


def test_logout(api_client_anon):
    # logout should work anyway, even when nobody is logged in
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/logout/')
    assert response.status_code == 200


def test_options_preflight_without_auth(api_client_anon, admin_user, admin_group):
    test_path = [('/api/', 'GET'),
                 (f'/api/{settings.API_VERSION}/users/{admin_user.pk}', 'GET'),
                 (f'/api/{settings.API_VERSION}/users/{admin_user.pk}', 'PATCH'),
                 (f'/api/{settings.API_VERSION}/groups/{admin_group.pk}', 'GET'),
                 (f'/api/{settings.API_VERSION}/cluster/k8s_apiserver', 'GET'),
                 (f'/api/{settings.API_VERSION}/login/', 'POST'),
                 ]
    for path, request_method in test_path:
        response = api_client_anon.options(path)
        assert 200 == response.status_code


@override_settings(SOCIALACCOUNT_PROVIDERS={'google': {
    'APP': {
        'secret': '123',
        'client_id': '456'
    },
    'SCOPE': ['profile', 'email'],
}})
def test_invalid_google_login(api_client_anon):
    """
    We have no valid OAuth credentials when running the test suite, but at least
    we can check that no crash happens when using this API call with fake data.
    """
    response = api_client_anon.post(f'/api/{settings.API_VERSION}/login_google/', {'access_token': 'foo', 'code': 'bar'})
    assert response.status_code == 400


def test_cluster(api_client):
    for stat in ClusterInfoView.stats.keys():
        response = api_client.get(f'/api/{settings.API_VERSION}/cluster/{stat}/')
        assert 200 == response.status_code
        data = response.json()
        assert stat in data.keys()
        assert data[stat] is not None


@override_settings(ALLOWED_URLS=['http://testserver', ])
def test_cors_single_origin(api_client):
    headers = {'Origin': 'http://testserver'}
    relative_urls = [f'/api/{settings.API_VERSION}/login/', f'/api/{settings.API_VERSION}/cluster/portal_version/']
    for url in relative_urls:
        response = api_client.get(url, headers=headers)
        assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'
        assert response.headers['Access-Control-Allow-Credentials'] == 'true'


@override_settings(ALLOWED_URLS=['http://testserver', 'https://example.org:8000'])
def test_cors_multiple_allowed(api_client):
    headers = {'Origin': 'http://testserver'}
    response = api_client.get(f'/api/{settings.API_VERSION}/cluster/portal_version/', headers=headers)
    assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'


def test_cluster_invalid(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/cluster/foobar/')
    assert response.status_code == 404


def test_webapp_user_not_in_group(api_client):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 404


def test_webapp_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/777/')
    assert response.status_code == 404


def test_webapp_invisible(api_client, admin_group):
    app1 = WebApplication(name="app1", link_show=False,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 404


def test_webapp(api_client, admin_group):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['link_name'] == 'app1'
    assert data['link_url'] == 'http://www.heise.de'
    assert data['category'] == "GENERIC"


def test_webapp_placeholders(api_client, admin_group, admin_user_with_k8s_system):
    app1 = WebApplication(name="app1", link_show=True,
                          link_name="app1", link_url="http://www.heise.de/{{{{namespace}}}}/{{{{serviceaccount}}}}")
    app1.save()
    admin_group.can_web_applications.add(app1)

    response = api_client.get(f'/api/{settings.API_VERSION}/webapps/{app1.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['link_url'] == 'http://www.heise.de/kube-system/default'


def test_group(api_client, admin_group):
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/{admin_group.pk}/')
    assert response.status_code == 200

    data = response.json()
    assert data['name'] == admin_group.name


def test_group_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/777/')
    assert response.status_code == 404


def test_group_non_member(api_client):
    group1 = PortalGroup(name="group1")
    group1.save()
    response = api_client.get(f'/api/{settings.API_VERSION}/groups/{group1.pk}/')
    assert response.status_code == 404


def test_user(api_client, admin_user_with_k8s_system):
    user_attr_expected = [
        'firstname',
        'name',
        'username',
        'primary_email',
        'all_emails',
        'admin',
        'k8s_accounts',
        'k8s_token',
    ]

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user_with_k8s_system.pk}/')
    assert response.status_code == 200
    data = response.json()

    assert True is data['admin']

    for key in user_attr_expected:
        assert key in data

    assert data["user_id"] == 1
    assert data["group_ids"] == [1]
    assert data['all_emails'] == ['admin@example.com']
    assert data['k8s_accounts'] == [{'namespace': 'kube-system', 'service_account': 'default'},]



def test_patch_user(api_client, admin_user):
    data_mock = {"primary_email": "foo@bar.de"}

    response = api_client.patch(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/', data_mock)

    updated_primary_email = json.loads(response.text)['primary_email']
    assert updated_primary_email == data_mock['primary_email']
    assert response.status_code == 200

def test_user_all_email_adrs(api_client, admin_user):
    admin_user.email ="a@b.de"
    admin_user.alt_mails = ["c@d.de", "e@f.de"]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/')

    all_emails = json.loads(response.text)['all_emails']
    assert all_emails == ["a@b.de", "c@d.de", "e@f.de"]
    assert response.status_code == 200

def test_user_all_email_adrs_empty_alt(api_client, admin_user):
    admin_user.alt_mails = None
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/users/{admin_user.pk}/')

    all_emails = json.loads(response.text)['all_emails']
    assert all_emails == ["admin@example.com"]
    assert response.status_code == 200


def test_patch_user_invalid_id(api_client):
    response = api_client.patch(f'/api/{settings.API_VERSION}/users/777/', {})
    assert response.status_code == 404


def test_patch_user_not_himself(api_client, second_user):
    response = api_client.patch(f'/api/{settings.API_VERSION}/users/{second_user.pk}/', {})
    assert response.status_code == 404


def test_user_invalid_id(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/777/')
    assert response.status_code == 404


def test_get_user_not_himself(api_client, second_user):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/{second_user.pk}/')
    assert response.status_code == 404


def test_no_general_user_list(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/users/')
    assert response.status_code == 404


def test_user_pods_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/foobar/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/pods/kube-system/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    names = [record['name'] for record in data]
    assert len(names) > 0


def test_user_pods_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/pods/default/')
    assert 404 == response.status_code


def test_user_deployments_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/foobar/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/kube-system/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "coredns" in data[0]['name']


def test_user_deployments_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/deployments/default/')
    assert 404 == response.status_code


def test_user_deployments_create(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    old_count = len(api.get_namespaced_deployments("kube-system"))
    try:
        response = api_client.post(f'/api/{settings.API_VERSION}/deployments/kube-system/',
                             {'name': 'test-deployment',
                              'replicas': 1,
                              'matchLabels': {'app': 'webapp'},
                              'template': {
                                  'name': 'webapp',
                                  'labels': {'app': 'webapp'},
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


def test_user_services_create(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    old_count = len(api.get_namespaced_services("kube-system"))
    try:
        response = api_client.post(f'/api/{settings.API_VERSION}/services/kube-system/', {
            'name': 'my-service',
            'type': 'NodePort',
            'selector': {'app': 'kubeportal'},
            'ports': [{'port': 8000, 'protocol': 'TCP'}]
        })
        assert 201 == response.status_code
        new_count = len(api.get_namespaced_services("kube-system"))
        assert old_count + 1 == new_count
    finally:
        api.core_v1.delete_namespaced_service(name="my-service", namespace="kube-system")


def test_user_services_create_wrong_ns(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/services/xyz/', {
        'name': 'my-service',
        'type': 'NodePort',
        'selector': {'app': 'kubeportal'},
        'ports': [{'port': 8000, 'protocol': 'TCP'}]
    })
    assert 404 == response.status_code


def test_user_ingresses_create(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()
    old_count = len(api.get_namespaced_ingresses("kube-system"))
    try:
        response = api_client.post(f'/api/{settings.API_VERSION}/ingresses/kube-system/',
                             {'name': 'test-ingress',
                              'annotations': {
                                  'nginx.ingress.kubernetes.io/rewrite-target': '/',
                              },
                              'tls': True,
                              'rules': {
                                  'www.example.com': {
                                      '/svc': {
                                          'service_name': 'my-svc',
                                          'service_port': 8000
                                      },
                                      '/docs': {
                                          'service_name': 'my-docs-svc',
                                          'service_port': 5000
                                      }
                                  }
                              }})
        assert 201 == response.status_code
        new_count = len(api.get_namespaced_ingresses("kube-system"))
        assert old_count + 1 == new_count
    finally:
        api.net_v1.delete_namespaced_ingress(name="test-ingress", namespace="kube-system")


def test_user_deployments_create_wrong_ns(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/deployments/xyz/',
                         {'name': 'test-deployment',
                          'replicas': 1,
                          'matchLabels': {'app': 'webapp'},
                          'template': {
                              'name': 'webapp',
                              'labels': {'app': 'webapp'},
                              'containers': [{
                                  'name': 'busybox',
                                  'image': 'busybox'
                              }, ]
                          }})
    assert 404 == response.status_code


def test_user_ingresses_create_wrong_ns(api_client):
    response = api_client.post(f'/api/{settings.API_VERSION}/ingresses/xyz/',
                         {'name': 'test-ingress',
                          'annotations': {
                              'nginx.ingress.kubernetes.io/rewrite-target': '/',
                          },
                          'tls': True,
                          'rules': {
                              'www.example.com': {
                                  '/svc': {
                                      'service_name': 'my-svc',
                                      'service_port': 8000
                                  },
                                  '/docs': {
                                      'service_name': 'my-docs-svc',
                                      'service_port': 5000
                                  }
                              }
                          }})
    assert 404 == response.status_code


def test_user_services_list(api_client, admin_user):
    run_minikube_sync()
    system_namespace = KubernetesNamespace.objects.get(name="kube-system")
    admin_user.service_account = system_namespace.service_accounts.all()[0]
    admin_user.save()

    response = api_client.get(f'/api/{settings.API_VERSION}/services/foobar/')
    assert 404 == response.status_code

    response = api_client.get(f'/api/{settings.API_VERSION}/services/kube-system/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "kube-dns" in data[0]['name']


def test_user_services_list_no_k8s(api_client):
    response = api_client.get(f'/api/{settings.API_VERSION}/services/default/')
    assert 404 == response.status_code


def test_user_ingresses_list(api_client, admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/ingresses/default/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    assert "test-ingress-1" == data[0]['name']


def test_user_ingresses_list_no_k8s(api_client):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/ingresses/default/')
    assert 404 == response.status_code


def test_ingress_list(api_client, admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")
    apply_k8s_yml(BASE_DIR + "fixtures/ingress2.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/ingresses/default/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    host_names = [list(el["rules"].keys()) for el in data]
    assert [["visbert.demo.datexis.com"], ["tasty.demo.datexis.com"]] == host_names


def test_ingress_list_illegal_ns(api_client, admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")
    apply_k8s_yml(BASE_DIR + "fixtures/ingress2.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/ingresses/foobar/')
    assert 404 == response.status_code


def test_ingresshosts_list(api_client, admin_user_with_k8s):
    apply_k8s_yml(BASE_DIR + "fixtures/ingress1.yml")
    apply_k8s_yml(BASE_DIR + "fixtures/ingress2.yml")

    response = api_client.get(f'/api/{settings.API_VERSION}/ingresshosts/')
    assert 200 == response.status_code
    data = json.loads(response.content)
    for check_host in ["visbert.demo.datexis.com", "tasty.demo.datexis.com"]:
        assert check_host in data


def test_logout(api_client, admin_user):
    response = api_client.post(f'/api/{settings.API_VERSION}/logout/')
    assert response.status_code == 200
