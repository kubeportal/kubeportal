from django.test import override_settings
from rest_framework.test import RequestsClient
from kubeportal.tests import AdminLoggedOutTestCase, admin_data, admin_clear_password
from kubeportal.api.views import ClusterViewSet
from kubeportal.settings import API_VERSION
from kubeportal.models import WebApplication, PortalGroup

from django.contrib.auth import get_user_model

User = get_user_model()

class ApiTestCase(AdminLoggedOutTestCase):
    '''
    We take the more complicated way here, and implement the API tests
    with Python requests. This ensures that we are getting as close as possible
    to 'real' API clients, e.g. from JavaScript.
    '''
    def setUp(self):
        super().setUp()
        self.client = RequestsClient()

        # Obtain the CSRF token for later POST requests
        response = self.get('/')
        self.assertEquals(response.status_code, 200)
        self.csrftoken = response.cookies['csrftoken']

    def get(self, relative_url):
        return self.client.get('http://testserver' + relative_url)

    def patch(self, relative_url, data):
        return self.client.patch('http://testserver' + relative_url,
                                json=data,
                                headers={'X-CSRFToken': self.csrftoken})

    def post(self, relative_url, data={}):
        return self.client.post('http://testserver' + relative_url,
                                json=data,
                                headers={'X-CSRFToken': self.csrftoken})

    def api_login(self):
        response = self.post(F'/api/{API_VERSION}/login', {'username': admin_data['username'], 'password': admin_clear_password})
        self.assertEquals(response.status_code, 200)
        # The login API call returns the JWT + extra information as JSON in the body, but also sets a cookie with the JWT.
        # This means that for all test cases here, the JWT must not handed over explicitely,
        # since the Python http client has the cookie anyway.
        assert('kubeportal-auth' in response.cookies)
        data = response.json()
        self.assertEquals(2, len(data))
        self.assertIn('firstname', data)
        self.assertIn('id', data)
        self.assertEquals(data['id'], self.admin.pk)


class ApiAnonymous(ApiTestCase):
    '''
    Tests for API functionality when nobody is logged in.
    '''
    def setUp(self):
        super().setUp()

    def test_api_wrong_login(self):
        response = self.post(F'/api/{API_VERSION}/login', {'username': admin_data['username'], 'password': 'blabla'})
        self.assertEquals(response.status_code, 400)

    def test_cluster_denied(self):
        for stat in ClusterViewSet.stats.keys():
            with self.subTest(stat=stat):
                response = self.get(F'/api/{API_VERSION}/cluster/{stat}')
                self.assertEquals(response.status_code, 401)

    def test_webapp_denied(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(F'/api/{API_VERSION}/webapps/{app1.pk}')
        self.assertEquals(response.status_code, 401)

    def test_user_webapps_denied(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(F'/api/{API_VERSION}/users/{self.admin.pk}/webapps')
        self.assertEquals(response.status_code, 401)

    def test_group_denied(self):
        response = self.get(F'/api/{API_VERSION}/groups/{self.admin_group.pk}')
        self.assertEquals(response.status_code, 401)

    def test_user_groups_denied(self):
        response = self.get(F'/api/{API_VERSION}/users/{self.admin.pk}/groups')
        self.assertEquals(response.status_code, 401)

    def test_logout(self):
        # logout should work anyway, even when nobody is logged in
        response = self.post(F'/api/{API_VERSION}/logout')
        self.assertEquals(response.status_code, 200)

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
        response = self.post(F'/api/{API_VERSION}/login_google', {'access_token': 'foo', 'code': 'bar'})
        self.assertEquals(response.status_code, 400)

class ApiLocalUser(ApiTestCase):
    '''
    Tests for API functionality when a local Django user is logged in.
    '''
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
                response = self.get(F'/api/{API_VERSION}/cluster/{stat}')
                self.assertEquals(response.status_code, 200)
                data = response.json()
                self.assertIn('value', data.keys())
                self.assertIsNotNone(data['value'])

    def test_cluster_invalid(self):
        response = self.get(F'/api/{API_VERSION}/cluster/foobar')
        self.assertEquals(response.status_code, 404)

    def test_webapp_user_not_in_group(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()

        response = self.get(F'/api/{API_VERSION}/webapps/{app1.pk}')
        self.assertEquals(response.status_code, 403)

    def test_webapp_invalid_id(self):
        response = self.get(F'/api/{API_VERSION}/webapps/777')
        self.assertEquals(response.status_code, 404)


    def test_webapp_invisible(self):
        app1 = WebApplication(name="app1", link_show=False, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(F'/api/{API_VERSION}/webapps/{app1.pk}')
        self.assertEquals(response.status_code, 403)


    def test_webapp(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        self.admin_group.can_web_applications.add(app1)

        response = self.get(F'/api/{API_VERSION}/webapps/{app1.pk}')
        self.assertEquals(response.status_code, 200)

        data = response.json()
        self.assertEquals(data['link_name'], 'app1')
        self.assertEquals(data['link_url'], 'http://www.heise.de')

    def test_user_webapps(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        app2 = WebApplication(name="app2", link_show=True, link_name="app2", link_url="http://www.spiegel.de")
        app2.save()
        app3 = WebApplication(name="app3", link_show=False, link_name="app3", link_url="http://www.crappydemo.de")
        app3.save()
        app4 = WebApplication(name="app4", link_show=True, link_name="app4", link_url="http://www.unrelatedapp.de")
        app4.save()
        self.admin_group.can_web_applications.add(app1)
        self.admin_group.can_web_applications.add(app2)
        self.admin_group.can_web_applications.add(app3)

        response = self.get(F'/api/{API_VERSION}/users/{self.admin.pk}/webapps')
        self.assertEquals(response.status_code, 200)
        data = response.json()
        self.assertIn({'link_name': 'app1', 'link_url': 'http://www.heise.de'}, data)
        self.assertIn({'link_name': 'app2', 'link_url': 'http://www.spiegel.de'}, data)
        self.assertNotIn({'link_name': 'app3', 'link_url': 'http://www.crappydemo.de'}, data)
        self.assertNotIn({'link_name': 'app4', 'link_url': 'http://www.unrelatedapp.de'}, data)


    def test_user_webapps_invalid_id(self):
        response = self.get(F'/api/{API_VERSION}/users/777/webapps')
        self.assertEquals(response.status_code, 403)

    def test_user_groups(self):
        group1 = PortalGroup(name="group1")
        group1.save()
        group2 = PortalGroup(name="group2")
        group2.save()

        self.admin.portal_groups.add(group1)
        self.admin.portal_groups.add(group2)

        response = self.get(F'/api/{API_VERSION}/users/{self.admin.pk}/groups')
        self.assertEquals(response.status_code, 200)
        data = response.json()
        for entry in data:
            self.assertIn('name', entry.keys())
        self.assertEquals(4, len(data))  #  Auto group "all users", Test case group "Admins", plus 2 extra

    def test_group(self):
        response = self.get(F'/api/{API_VERSION}/groups/{self.admin_group.pk}')
        self.assertEquals(response.status_code, 200)

        data = response.json()
        self.assertEquals(data['name'], self.admin_group_name)

    def test_group_invalid_id(self):
        response = self.get(F'/api/{API_VERSION}/groups/777')
        self.assertEquals(response.status_code, 404)


    def test_group_non_member(self):
        group1 = PortalGroup(name="group1")
        group1.save()

        response = self.get(F'/api/{API_VERSION}/groups/{group1.pk}')
        self.assertEquals(response.status_code, 403)

    def test_group_invalid_id(self):
        response = self.get(F'/api/{API_VERSION}/users/777/groups')
        self.assertEquals(response.status_code, 403)


    def test_user(self):

        response = self.get(F'/api/{API_VERSION}/users/{self.admin.pk}')
        self.assertEquals(response.status_code, 200)
        data = response.json()

        self.assertIs(True, data['admin'])

        for key in self.user_attr_expected:
            with self.subTest(key=key):
                self.assertIn(key, data)

    def test_patch_user(self):
        # The implementation of correct patch() calls here failed,
        # the HTML-based version in the dev server works, however.
        # Somehow the PATCH request body sent here gets lost on the
        # way to the DRF code, even the serializer validator does
        # not see it
        #
        # We therefore restrict ourselves here to simple error cases.
        pass

    def test_patch_user_invalid_id(self):
        response = self.patch(F'/api/{API_VERSION}/users/777', {})
        self.assertEquals(response.status_code, 404)

    def test_patch_user_not_himself(self):
        u = User()
        u.save()

        response = self.patch(F'/api/{API_VERSION}/users/{u.pk}', {})
        self.assertEquals(response.status_code, 403)

    def test_user_invalid_id(self):
        response = self.get(F'/api/{API_VERSION}/users/777')
        self.assertEquals(response.status_code, 404)

    def test_user_not_himself(self):
        u = User()
        u.save()

        response = self.get(F'/api/{API_VERSION}/users/{u.pk}')
        self.assertEquals(response.status_code, 403)

    def test_no_general_user_list(self):
        response = self.get(F'/api/{API_VERSION}/users')
        self.assertEquals(response.status_code, 404)

    def test_no_general_webapp_list(self):
        response = self.get(F'/api/{API_VERSION}/webapps')
        self.assertEquals(response.status_code, 404)

    def test_no_general_group_list(self):
        response = self.get(F'/api/{API_VERSION}/groups')
        self.assertEquals(response.status_code, 404)


class ApiLogout(ApiTestCase):
    '''
    Tests for API logout functionality when a local Django user is logged in.
    '''
    def setUp(self):
        super().setUp()
        self.api_login()

    def test_logout(self):
        response = self.post(F'/api/{API_VERSION}/logout')
        self.assertEquals(response.status_code, 200)

