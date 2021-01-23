from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import RequestsClient
from kubernetes import utils as k8s_utils

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedOutTestCase, admin_data, admin_clear_password
from kubeportal.api.views import ClusterInfoView
from kubeportal.k8s import kubernetes_api as api
from django.conf import settings
import logging
import json
import os

logger = logging.getLogger('KubePortal')

User = get_user_model()
API_VERSION = settings.API_VERSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


class ApiTestCase(AdminLoggedOutTestCase):
    """
    We take the more complicated way here, and implement the API tests
    with Python requests. This ensures that we are getting as close as possible
    to 'real' API clients, e.g. from JavaScript.

    CRSF token and JWT are transported as cookie by default, in Django.
    The HTTP verb methods allow to override this and add according headers
    with the information. This is intended to support testing JavaScript AJAX calls,
    with seem to have trouble accessing the cookies sometimes. Ask @Kat-Hi.
    """

    def setUp(self):
        super().setUp()
        self.client = RequestsClient()
        self.jwt = None
        self.csrf = None

    def get(self, relative_url, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        return self.client.get('http://testserver' + relative_url, headers=headers)

    def patch(self, relative_url, data, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        if self.csrf:
            headers['X-CSRFToken'] = self.csrf
        return self.client.patch('http://testserver' + relative_url,
                                 json=data, headers=headers)

    def post(self, relative_url, data=None, headers={}):
        if self.jwt:
            headers["Authorization"] = "Bearer " + self.jwt
        if self.csrf:
            headers['X-CSRFToken'] = self.csrf
        return self.client.post('http://testserver' + relative_url,
                                json=data, headers=headers)

    def options(self, relative_url, headers={}):
        return self.client.options('http://testserver' + relative_url)

    def api_login(self):
        response = self.post(f'/api/{API_VERSION}/login/',
                             {'username': admin_data['username'], 'password': admin_clear_password})
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        self.jwt = data['access_token']


class ApiAnonymous(ApiTestCase):
    """
    Tests for API functionality when nobody is logged in.
    """

    def setUp(self):
        super().setUp()

    def test_api_bootstrap(self):
        response = self.get(f'/api/')
        assert response.status_code == 200
        data = response.json()
        assert 3 == len(data)
        assert 'csrf_token' in data
        assert 'portal_version' in data
        assert 'default_api_version' in data
        default_api_version = data['default_api_version']
        # check if given default API version makes sense
        # login path response tells us to use something else than GET
        response = self.get(f'/api/{default_api_version}/login/')
        assert response.status_code == 405

    def test_api_login(self):
        response = self.post(f'/api/{API_VERSION}/login/',
                             {'username': admin_data['username'], 'password': admin_clear_password})
        assert response.status_code == 200
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
        assert data['user_id'] == self.admin.pk

    def test_api_wrong_login(self):
        response = self.post(f'/api/{API_VERSION}/login/', {'username': admin_data['username'], 'password': 'blabla'})
        assert response.status_code == 400

    def test_js_api_bearer_auth(self):
        """
        Disable the cookie-based authentication and test the bearer
        auth with the token returned.
        """
        # Get JWT token
        response = self.post(f'/api/{API_VERSION}/login/',
                             {'username': admin_data['username'], 'password': admin_clear_password})
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        jwt = data['access_token']
        # Disable auth cookie
        del (self.client.cookies['kubeportal-auth'])
        # Simulate JS code calling, add Bearer token
        headers = {'Origin': 'http://testserver', 'Authorization': f'Bearer {jwt}'}
        response = self.get(f'/api/{API_VERSION}/cluster/portal_version/', headers=headers)
        assert response.status_code == 200

    def test_cluster_denied(self):
        for stat in ClusterInfoView.stats.keys():
            with self.subTest(stat=stat):
                response = self.get(f'/api/{API_VERSION}/cluster/{stat}/')
                assert response.status_code == 401

    def test_single_webapp_denied(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        assert response.status_code == 401

    def test_webapps_denied(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        assert response.status_code == 401

    def test_single_group_denied(self):
        response = self.get(f'/api/{API_VERSION}/groups/{self.admin_group.pk}/')
        assert response.status_code == 401

    def test_groups_denied(self):
        group1 = PortalGroup(name="group1")
        group1.save()
        response = self.get(f'/api/{API_VERSION}/groups/{group1.pk}/')
        assert response.status_code == 401

    def test_pods_denied(self):
        response = self.get(f'/api/{API_VERSION}/pods/kube-system/')
        assert response.status_code == 401

    def test_ingresses_denied(self):
        response = self.get(f'/api/{API_VERSION}/ingresses/default/')
        assert response.status_code == 401

    def test_ingresshosts_denied(self):
        response = self.get(f'/api/{API_VERSION}/ingresshosts/')
        assert response.status_code == 401

    def test_deployments_denied(self):
        response = self.get(f'/api/{API_VERSION}/deployments/default/')
        assert response.status_code == 401

    def test_services_denied(self):
        response = self.get(f'/api/{API_VERSION}/services/default/')
        assert response.status_code == 401

    def test_logout(self):
        # logout should work anyway, even when nobody is logged in
        response = self.post(f'/api/{API_VERSION}/logout/')
        assert response.status_code == 200

    def test_options_preflight_without_auth(self):
        test_path = [('/api/', 'GET'),
                     (f'/api/{API_VERSION}/users/{self.admin.pk}', 'GET'),
                     (f'/api/{API_VERSION}/users/{self.admin.pk}', 'PATCH'),
                     (f'/api/{API_VERSION}/groups/{self.admin_group.pk}', 'GET'),
                     (f'/api/{API_VERSION}/cluster/k8s_apiserver', 'GET'),
                     (f'/api/{API_VERSION}/login/', 'POST'),
                     ]
        for path, request_method in test_path:
            with self.subTest(path=path):
                response = self.options(path)
                assert 200 == response.status_code

    @override_settings(SOCIALACCOUNT_PROVIDERS={'google': {
        'APP': {
            'secret': '123',
            'client_id': '456'
        },
        'SCOPE': ['profile', 'email'],
    }})
    def test_invalid_google_login(self):
        """
        We have no valid OAuth credentials when running the test suite, but at least
        we can check that no crash happens when using this API call with fake data.
        """
        response = self.post(f'/api/{API_VERSION}/login_google/', {'access_token': 'foo', 'code': 'bar'})
        assert response.status_code == 400


class ApiLocalUser(ApiTestCase):
    """
    Tests for API functionality when a local Django user is logged in.
    """
    user_attr_expected = [
        'firstname',
        'name',
        'username',
        'primary_email',
        'all_emails',
        'admin',
        'k8s_serviceaccount',
        'k8s_namespace',
        'k8s_token',
    ]

    def _apply_yml(self, path):
        try:
            k8s_utils.create_from_yaml(api.api_client, path)
        except k8s_utils.FailToCreateError as e:
            if e.api_exceptions[0].reason == "Conflict":
                pass  # test namespace still exists in Minikube from another run
            else:
                raise e

    def setUp(self):
        super().setUp()
        self.api_login()

    def test_cluster(self):
        for stat in ClusterInfoView.stats.keys():
            with self.subTest(stat=stat):
                response = self.get(f'/api/{API_VERSION}/cluster/{stat}/')
                assert 200 == response.status_code
                data = response.json()
                assert stat in data.keys()
                assert data[stat] is not None

    @override_settings(ALLOWED_URLS=['http://testserver', ])
    def test_cors_single_origin(self):
        headers = {'Origin': 'http://testserver'}
        relative_urls = [f'/api/{API_VERSION}/login/', f'/api/{API_VERSION}/cluster/portal_version/']
        for url in relative_urls:
            with self.subTest(url=url):
                response = self.get(url, headers=headers)
                assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'
                assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    @override_settings(ALLOWED_URLS=['http://testserver', 'https://example.org:8000'])
    def test_cors_multiple_allowed(self):
        headers = {'Origin': 'http://testserver'}
        response = self.get(f'/api/{API_VERSION}/cluster/portal_version/', headers=headers)
        assert response.headers['Access-Control-Allow-Origin'] == 'http://testserver'

    def test_cluster_invalid(self):
        response = self.get(f'/api/{API_VERSION}/cluster/foobar/')
        assert response.status_code == 404

    def test_webapp_user_not_in_group(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        assert response.status_code == 404

    def test_webapp_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/webapps/777/')
        assert response.status_code == 404

    def test_webapp_invisible(self):
        app1 = WebApplication(name="app1", link_show=False,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        assert response.status_code == 404

    def test_webapp(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        assert response.status_code == 200

        data = response.json()
        assert data['link_name'] == 'app1'
        assert data['link_url'] == 'http://www.heise.de'

    def test_group(self):
        response = self.get(f'/api/{API_VERSION}/groups/{self.admin_group.pk}/')
        assert response.status_code == 200

        data = response.json()
        assert data['name'] == self.admin_group_name

    def test_group_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/groups/777/')
        assert response.status_code == 404

    def test_group_non_member(self):
        group1 = PortalGroup(name="group1")
        group1.save()
        response = self.get(f'/api/{API_VERSION}/groups/{group1.pk}/')
        assert response.status_code == 404

    def test_user(self):
        response = self.get(f'/api/{API_VERSION}/users/{self.admin.pk}/')
        assert response.status_code == 200
        data = response.json()

        assert True is data['admin']

        for key in self.user_attr_expected:
            with self.subTest(key=key):
                assert key in data

    def test_patch_user(self):
        data_mock = {"primary_email": "foo@bar.de"}

        response = self.patch(f'/api/{API_VERSION}/users/{self.admin.pk}/', data_mock)

        updated_primary_email = json.loads(response.text)['primary_email']
        assert updated_primary_email == data_mock['primary_email']
        assert response.status_code == 200

    def test_patch_user_invalid_id(self):
        response = self.patch(f'/api/{API_VERSION}/users/777/', {})
        assert response.status_code == 404

    def test_patch_user_not_himself(self):
        u = User()
        u.save()

        response = self.patch(f'/api/{API_VERSION}/users/{u.pk}/', {})
        assert response.status_code == 404

    def test_user_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/users/777/')
        assert response.status_code == 404

    def test_get_user_not_himself(self):
        u = User()
        u.save()

        response = self.get(f'/api/{API_VERSION}/users/{u.pk}/')
        assert response.status_code == 404

    def test_no_general_user_list(self):
        response = self.get(f'/api/{API_VERSION}/users/')
        assert response.status_code == 404

    def test_user_pods_list(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()

        response = self.get(f'/api/{API_VERSION}/pods/foobar/')
        assert 404 == response.status_code

        response = self.get(f'/api/{API_VERSION}/pods/kube-system/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        names = [record['name'] for record in data]
        assert len(names) > 0

    def test_user_pods_list_no_k8s(self):
        response = self.get(f'/api/{API_VERSION}/pods/default/')
        assert 404 == response.status_code

    def test_user_deployments_list(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()

        response = self.get(f'/api/{API_VERSION}/deployments/foobar/')
        assert 404 == response.status_code

        response = self.get(f'/api/{API_VERSION}/deployments/kube-system/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        assert "coredns" in data[0]['name']

    def test_user_deployments_list_no_k8s(self):
        response = self.get(f'/api/{API_VERSION}/deployments/default/')
        assert 404 == response.status_code

    def test_user_deployments_create(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()
        old_count = len(api.get_namespaced_deployments("kube-system"))
        try:
            response = self.post(f'/api/{API_VERSION}/deployments/kube-system/',
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

    def test_user_services_create(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()
        old_count = len(api.get_namespaced_services("kube-system"))
        try:
            response = self.post(f'/api/{API_VERSION}/services/kube-system/', {
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

    def test_user_services_create_wrong_ns(self):
        response = self.post(f'/api/{API_VERSION}/services/xyz/', {
            'name': 'my-service',
            'type': 'NodePort',
            'selector': {'app': 'kubeportal'},
            'ports': [{'port': 8000, 'protocol': 'TCP'}]
        })
        assert 404 == response.status_code

    def test_user_ingresses_create(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()
        old_count = len(api.get_namespaced_ingresses("kube-system"))
        try:
            response = self.post(f'/api/{API_VERSION}/ingresses/kube-system/',
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

    def test_user_deployments_create_wrong_ns(self):
        response = self.post(f'/api/{API_VERSION}/deployments/xyz/',
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

    def test_user_ingresses_create_wrong_ns(self):
        response = self.post(f'/api/{API_VERSION}/ingresses/xyz/',
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

    def test_user_services_list(self):
        self._call_sync()
        system_namespace = KubernetesNamespace.objects.get(name="kube-system")
        self.admin.service_account = system_namespace.service_accounts.all()[0]
        self.admin.save()

        response = self.get(f'/api/{API_VERSION}/services/foobar/')
        assert 404 == response.status_code

        response = self.get(f'/api/{API_VERSION}/services/kube-system/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        assert "kube-dns" in data[0]['name']

    def test_user_services_list_no_k8s(self):
        response = self.get(f'/api/{API_VERSION}/services/default/')
        assert 404 == response.status_code

    def test_user_ingresses_list(self):
        self._call_sync()
        default_namespace = KubernetesNamespace.objects.get(name="default")
        self.admin.service_account = default_namespace.service_accounts.all()[0]
        self.admin.save()

        self._apply_yml(BASE_DIR + "fixtures/ingress1.yml")

        response = self.get(f'/api/{API_VERSION}/ingresses/default/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        assert "test-ingress-1" == data[0]['name']

    def test_user_ingresses_list_no_k8s(self):
        self._apply_yml(BASE_DIR + "fixtures/ingress1.yml")

        response = self.get(f'/api/{API_VERSION}/ingresses/default/')
        assert 404 == response.status_code

    def test_ingress_list(self):
        self._call_sync()
        default_namespace = KubernetesNamespace.objects.get(name="default")
        self.admin.service_account = default_namespace.service_accounts.all()[0]
        self.admin.save()

        self._apply_yml(BASE_DIR + "fixtures/ingress1.yml")
        self._apply_yml(BASE_DIR + "fixtures/ingress2.yml")

        response = self.get(f'/api/{API_VERSION}/ingresses/default/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        host_names = [list(el["rules"].keys()) for el in data]
        assert [["visbert.demo.datexis.com"], ["tasty.demo.datexis.com"]] == host_names

    def test_ingress_list_illegal_ns(self):
        self._call_sync()
        default_namespace = KubernetesNamespace.objects.get(name="default")
        self.admin.service_account = default_namespace.service_accounts.all()[0]
        self.admin.save()

        self._apply_yml(BASE_DIR + "fixtures/ingress1.yml")
        self._apply_yml(BASE_DIR + "fixtures/ingress2.yml")

        response = self.get(f'/api/{API_VERSION}/ingresses/foobar/')
        assert 404 == response.status_code

    def test_ingresshosts_list(self):
        self._call_sync()
        default_namespace = KubernetesNamespace.objects.get(name="default")
        self.admin.service_account = default_namespace.service_accounts.all()[0]
        self.admin.save()

        self._apply_yml(BASE_DIR + "fixtures/ingress1.yml")
        self._apply_yml(BASE_DIR + "fixtures/ingress2.yml")

        response = self.get(f'/api/{API_VERSION}/ingresshosts/')
        assert 200 == response.status_code
        data = json.loads(response.content)
        for check_host in ["visbert.demo.datexis.com", "tasty.demo.datexis.com"]:
            assert check_host in data


class ApiLogout(ApiTestCase):
    """
    Tests for API logout functionality when a local Django user is logged in.
    """

    def setUp(self):
        super().setUp()
        self.api_login()

    def test_logout(self):
        response = self.post(f'/api/{API_VERSION}/logout/')
        assert response.status_code == 200
