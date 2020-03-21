'''
    Test code for authentication-related code parts.

    Most parts are copied from https://github.com/juanifioren/django-oidc-provider/tree/master/oidc_provider/tests.
'''

from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from oidc_provider.views import userinfo, TokenIntrospectionView, AuthorizeView
from oidc_provider.models import Client, ResponseType, Token
from oidc_provider.lib.utils.token import create_token, create_id_token
from . import AdminLoggedOutTestCase, admin_data
from urllib.parse import urlencode
import uuid
import random
from django.utils import timezone
import json


class FrontendAuth(AdminLoggedOutTestCase):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client = Client()
        self.client.name = 'Some Client'
        self.client.client_id = str(random.randint(1, 999999)).zfill(6)
        self.client.client_secret = str(random.randint(1, 999999)).zfill(6)
        self.client.redirect_uris = ['http://example.com/']
        self.client.require_consent = False
        self.client.save()
        self.client.response_types.add(ResponseType.objects.get(value='code'))
        self.state = uuid.uuid4().hex

    def _perform_oidc_login(self):
        data = {
            'client_id': self.client.client_id,
            'redirect_uri': self.client.default_redirect_uri,
            'response_type': 'code',
            'scope': 'openid email',
            'state': self.state,
            'allow': 'Accept',
        }

        query_str = urlencode(data).replace('+', '%20')
        url = reverse('oidc_provider:authorize') + '/?' + query_str
        request = self.factory.get(url)
        request.user = self.admin
        response = AuthorizeView.as_view()(request)
        self.assertTrue(
            response['Location'].startswith(self.client.default_redirect_uri),
            msg='Different redirect_uri returned')
        self.assertTrue(response.status_code, 302)



    # def test_token_introspection(self):
    #     '''
    #     Token introspection is done by the resource server when a request comes in,
    #     and is provided by us. Alle access checks happen here.
    #     '''
    #     url = reverse('oidc_provider:token-introspection')
    #     data = {
    #         'client_id': self.client.client_id,
    #         'client_secret': self.client.client_secret,
    #         'token': self.token.access_token,
    #     }
    #     request = self.factory.post(url, data=urlencode(data),
    #                                 content_type='application/x-www-form-urlencoded')
    #     self.assertEquals(TokenIntrospectionView.as_view()(request).status_code, 200)


    # def test_userinfo(self):
    #     '''
    #         Simulates that the OIDC client application is fetching user information.
    #     '''
    #     url = reverse('oidc_provider:userinfo')
    #     request = self.factory.get(url)
    #     request.META['HTTP_AUTHORIZATION'] = 'Bearer ' + self.token.access_token
    #     response = userinfo(request)
    #     self.assertEquals(json.loads(response.content)['email'], admin_data['email'])


