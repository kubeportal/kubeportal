from django.test import override_settings
from rest_framework.test import RequestsClient
from kubeportal.tests import AdminLoggedOutTestCase, admin_data, admin_clear_password
from kubeportal.api.views import StatisticsView


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

    def post(self, relative_url, data={}):
        return self.client.post('http://testserver' + relative_url,
                                json=data,
                                headers={'X-CSRFToken': self.csrftoken})

    def api_login(self):
        response = self.post('/api/login', {'username': admin_data['username'], 'password': admin_clear_password})
        self.assertEquals(response.status_code, 200)
        # The login API call returns the JWT + extra information as JSON in the body, but also sets a cookie with the JWT.
        # This means that for all test cases here, the JWT must not handed over explicitely,
        # since the Python http client has the cookie anyway.
        self.jwt = response.json()["access_token"]
        assert('kubeportal-auth' in response.cookies)
        self.assertEquals(response.cookies['kubeportal-auth'], self.jwt)


class ApiAnonymous(ApiTestCase):
    '''
    Tests for API functionality when nobody is logged in.
    '''
    def setUp(self):
        super().setUp()

    def test_user_list_denied(self):
        response = self.get('/api/users/')
        self.assertEquals(response.status_code, 401)

    def test_logout(self):
        # logout should work anyway, even when nobody is logged in
        response = self.post('/api/logout')
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
        response = self.post('/api/login_google', {'access_token': 'foo', 'code': 'bar'})
        self.assertEquals(response.status_code, 400)

class ApiLocalUser(ApiTestCase):
    '''
    Tests for API functionality when a local Django user is logged in.
    '''
    def setUp(self):
        super().setUp()
        self.api_login()

    def test_user_list(self):
        response = self.get('/api/users/')
        self.assertEquals(response.status_code, 200)

    def test_stats(self):
        for stat in StatisticsView.stats.keys():
            with self.subTest(stat=stat):
                response = self.get('/api/statistics/{}'.format(stat))
                self.assertEquals(response.status_code, 200)


class ApiLogout(ApiTestCase):
    '''
    Tests for API logout functionality when a local Django user is logged in.
    '''
    def setUp(self):
        super().setUp()
        self.api_login()

    def test_logout(self):
        response = self.post('/api/logout')
        self.assertEquals(response.status_code, 200)

