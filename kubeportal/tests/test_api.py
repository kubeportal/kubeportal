from django.http import JsonResponse
from django.test import override_settings
from rest_framework.test import RequestsClient
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedOutTestCase, admin_data, admin_clear_password
from kubeportal.api.views import ClusterViewSet
from django.conf import settings
import logging
import json

logger = logging.getLogger('KubePortal')

from django.contrib.auth import get_user_model

User = get_user_model()
API_VERSION = settings.API_VERSION


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
        response = self.post(f'/api/{API_VERSION}/login/', {'username': admin_data['username'], 'password': admin_clear_password})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access_token', data)
        self.jwt = data['access_token']


class ApiAnonymous(ApiTestCase):
    """
    Tests for API functionality when nobody is logged in.
    """

    def setUp(self):
        super().setUp()

    def test_api_bootstrap(self):
        response = self.get(f'/api/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(3, len(data))
        self.assertIn('csrf_token', data)
        self.assertIn('portal_version', data)
        self.assertIn('default_api_version', data)
        default_api_version = data['default_api_version']
        # check if given default API version makes sense
        # login path response tells us to use something else than GET
        response = self.get(f'/api/{default_api_version}/login/')
        self.assertEqual(response.status_code, 405)

    def test_api_login(self):
        response = self.post(f'/api/{API_VERSION}/login/', {'username': admin_data['username'], 'password': admin_clear_password})
        self.assertEqual(response.status_code, 200)
        # JWT_AUTH_COOKIE not used
        #
        #self.assertIn('Set-Cookie', response.headers)
        #self.assertIn('kubeportal-auth=', response.headers['Set-Cookie'])
        #from http.cookies import SimpleCookie
        #cookie = SimpleCookie()
        #cookie.load(response.headers['Set-Cookie'])
        #self.assertEqual(cookie['kubeportal-auth']['path'], '/')
        #self.assertEqual(cookie['kubeportal-auth']['samesite'], 'Lax,')
        #self.assertEqual(cookie['kubeportal-auth']['httponly'], True)
        data = response.json()
        self.assertEqual(3, len(data))
        self.assertIn('firstname', data)
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.admin.pk)
        self.assertIn('access_token', data)

    def test_api_wrong_login(self):
        response = self.post(f'/api/{API_VERSION}/login/', {'username': admin_data['username'], 'password': 'blabla'})
        self.assertEqual(response.status_code, 400)

    def test_js_api_bearer_auth(self):
        """
        Disable the cookie-based authentication and test the bearer
        auth with the token returned.
        """
        # Get JWT token
        response = self.post(f'/api/{API_VERSION}/login/', {'username': admin_data['username'], 'password': admin_clear_password})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access_token', data)
        jwt = data['access_token']
        # Disable auth cookie
        del(self.client.cookies['kubeportal-auth'])
        # Simulate JS code calling, add Bearer token
        headers = {'Origin': 'http://testserver', 'Authorization': f'Bearer {jwt}'}
        response = self.get(f'/api/{API_VERSION}/cluster/portal_version/', headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_cluster_denied(self):
        for stat in ClusterViewSet.stats.keys():
            with self.subTest(stat=stat):
                response = self.get(f'/api/{API_VERSION}/cluster/{stat}/')
                self.assertEqual(response.status_code, 401)

    def test_webapp_denied(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        self.assertEqual(response.status_code, 401)

    def test_user_webapps_denied(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/users/{self.admin.pk}/webapps/')
        self.assertEqual(response.status_code, 401)

    def test_group_denied(self):
        response = self.get(f'/api/{API_VERSION}/groups/{self.admin_group.pk}/')
        self.assertEqual(response.status_code, 401)

    def test_user_groups_denied(self):
        response = self.get(f'/api/{API_VERSION}/groups/{self.admin_group.pk}/')
        self.assertEqual(response.status_code, 401)

    def test_logout(self):
        # logout should work anyway, even when nobody is logged in
        response = self.post(f'/api/{API_VERSION}/logout/')
        self.assertEqual(response.status_code, 200)

    def test_options_preflight_without_auth(self):
        test_path = [('/api/', 'GET'),
                     (f'/api/{API_VERSION}/users/{self.admin.pk}', 'GET'),
                     (f'/api/{API_VERSION}/users/{self.admin.pk}/webapps', 'GET'),
                     (f'/api/{API_VERSION}/users/{self.admin.pk}', 'PATCH'),
                     (f'/api/{API_VERSION}/groups/{self.admin_group.pk}', 'GET'),
                     (f'/api/{API_VERSION}/cluster/k8s_apiserver', 'GET'),
                     (f'/api/{API_VERSION}/login/', 'POST'),
        ]
        for path, request_method in test_path:
            with self.subTest(path=path):
                response = self.options(path)
                self.assertEqual(response.status_code, 200)

    @override_settings(SOCIALACCOUNT_PROVIDERS={'google': {
        'APP': {
            'secret': '123',
            'client_id': '456'
        },
        'SCOPE': ['profile', 'email'],
    }})
    def test_invalid_google_login(self):
        '''
        We have no valid OAuth credentials when running the test suite, but at least
        we can check that no crash happens when using this API call with fake data.
        '''
        response = self.post(f'/api/{API_VERSION}/login_google/', {'access_token': 'foo', 'code': 'bar'})
        self.assertEqual(response.status_code, 400)


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

    def setUp(self):
        super().setUp()
        self.api_login()

    def test_cluster(self):
        for stat in ClusterViewSet.stats.keys():
            with self.subTest(stat=stat):
                response = self.get(f'/api/{API_VERSION}/cluster/{stat}/')
                self.assertEqual(200, response.status_code)
                data = response.json()
                self.assertIn(stat, data.keys())
                self.assertIsNotNone(data[stat])

    @override_settings(ALLOWED_URLS=['http://testserver', ])
    def test_cors_single_origin(self):
        headers = {'Origin': 'http://testserver'}
        relative_urls = [f'/api/{API_VERSION}/login/', f'/api/{API_VERSION}/cluster/portal_version/']
        for url in relative_urls:
            with self.subTest(url=url):
                response = self.get(url, headers=headers)
                self.assertEqual(
                    response.headers['Access-Control-Allow-Origin'], 'http://testserver')
                self.assertEqual(
                    response.headers['Access-Control-Allow-Credentials'], 'true')

    @override_settings(ALLOWED_URLS=['http://testserver', 'https://example.org:8000'])
    def test_cors_multiple_allowed(self):
        headers = {'Origin': 'http://testserver'}
        response = self.get(f'/api/{API_VERSION}/cluster/portal_version/', headers=headers)
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'], 'http://testserver')

    def test_cluster_invalid(self):
        response = self.get(f'/api/{API_VERSION}/cluster/foobar/')
        self.assertEqual(response.status_code, 404)

    def test_webapp_user_not_in_group(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_webapp_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/webapps/777/')
        self.assertEqual(response.status_code, 404)

    def test_webapp_invisible(self):
        app1 = WebApplication(name="app1", link_show=False,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_webapp(self):
        app1 = WebApplication(name="app1", link_show=True,
                              link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(f'/api/{API_VERSION}/webapps/{app1.pk}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['link_name'], 'app1')
        self.assertEqual(data['link_url'], 'http://www.heise.de')

    def test_user_webapps(self):
        test_values = [('app1', True, "http://www.heise.de"),
                       ("app2", True, "http://www.spiegel.de"),
                       ("app3", False, "http://www.crappydemo.de"),
                       ("app4", True, "http://www.unrelatedapp.de"),
                       ]

        for name, link_show, link_url in test_values:
            app = WebApplication(name=name, link_show=link_show,
                                 link_name=name, link_url=link_url)
            app.save()
            if name != 'app4':
                self.admin_group.can_web_applications.add(app)

        response = self.get(f'/api/{API_VERSION}/users/{self.admin.pk}/webapps/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(
            {'link_name': 'app1', 'link_url': 'http://www.heise.de'}, data)
        self.assertIn(
            {'link_name': 'app2', 'link_url': 'http://www.spiegel.de'}, data)
        self.assertNotIn(
            {'link_name': 'app3', 'link_url': 'http://www.crappydemo.de'}, data)
        self.assertNotIn(
            {'link_name': 'app4', 'link_url': 'http://www.unrelatedapp.de'}, data)

    def test_user_webapps_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/users/777/webapps/')
        self.assertEqual(response.status_code, 403)

    def test_user_groups(self):
        group1 = PortalGroup(name="group1")
        group1.save()
        group2 = PortalGroup(name="group2")
        group2.save()

        self.admin.portal_groups.add(group1)
        self.admin.portal_groups.add(group2)

        response = self.get(f'/api/{API_VERSION}/users/{self.admin.pk}/groups/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for entry in data:
            self.assertIn('name', entry.keys())
        # Auto group "all users", Test case group "Admins", plus 2 extra
        self.assertEqual(4, len(data))

    def test_group(self):
        response = self.get(f'/api/{API_VERSION}/groups/{self.admin_group.pk}/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['name'], self.admin_group_name)

    def test_group_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/groups/777/')
        self.assertEqual(response.status_code, 404)

    def test_group_non_member(self):
        group1 = PortalGroup(name="group1")
        group1.save()
        response = self.get(f'/api/{API_VERSION}/groups/{group1.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_group_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/users/777/groups/')
        self.assertEqual(response.status_code, 403)

    def test_user(self):
        response = self.get(f'/api/{API_VERSION}/users/{self.admin.pk}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIs(True, data['admin'])

        for key in self.user_attr_expected:
            with self.subTest(key=key):
                self.assertIn(key, data)

    def test_patch_user(self):
        data_mock = {"primary_email": "foo@bar.de"}

        response = self.patch(f'/api/{API_VERSION}/users/{self.admin.pk}/', data_mock)

        updated_primary_email = json.loads(response.text)['primary_email']
        self.assertEqual(updated_primary_email, data_mock['primary_email'])
        self.assertEqual(response.status_code, 200)

    def test_patch_user_invalid_id(self):
        response = self.patch(f'/api/{API_VERSION}/users/777/', {})
        self.assertEqual(response.status_code, 404)

    def test_patch_user_not_himself(self):
        u = User()
        u.save()

        response = self.patch(f'/api/{API_VERSION}/users/{u.pk}/', {})
        self.assertEqual(response.status_code, 403)

    def test_user_invalid_id(self):
        response = self.get(f'/api/{API_VERSION}/users/777/')
        self.assertEqual(response.status_code, 404)

    def test_user_not_himself(self):
        u = User()
        u.save()

        response = self.get(f'/api/{API_VERSION}/users/{u.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_no_general_user_list(self):
        response = self.get(f'/api/{API_VERSION}/users/')
        self.assertEqual(response.status_code, 404)

    def test_no_general_webapp_list(self):
        response = self.get(f'/api/{API_VERSION}/webapps/')
        self.assertEqual(response.status_code, 404)

    def test_no_general_group_list(self):
        response = self.get(f'/api/{API_VERSION}/groups/')
        self.assertEqual(response.status_code, 404)


class ApiLogout(ApiTestCase):
    '''
    Tests for API logout functionality when a local Django user is logged in.
    '''

    def setUp(self):
        super().setUp()
        self.api_login()

    def test_logout(self):
        response = self.post(f'/api/{API_VERSION}/logout/')
        self.assertEqual(response.status_code, 200)
