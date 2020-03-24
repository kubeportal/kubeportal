'''
    Test code for authentication-related code parts.

    Most parts are copied from https://github.com/juanifioren/django-oidc-provider/tree/master/oidc_provider/tests.
'''

from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from oidc_provider.views import userinfo, TokenIntrospectionView, AuthorizeView
from oidc_provider.models import Client, ResponseType, Token
from oidc_provider.lib.utils.token import create_token, create_id_token
from . import AdminLoggedOutTestCase, admin_data
from urllib.parse import urlencode
from unittest.mock import patch
from kubeportal.models import WebApplication, Group
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

    def _authenticate(self):
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
        return AuthorizeView.as_view()(request)


    def _create_token(self):
        scope = ['openid', 'email']

        token = create_token(
            user=self.admin,
            client=self.client,
            scope=scope)

        id_token_dic = create_id_token(
            token=token,
            user=self.user,
            aud=self.client.client_id,
            nonce='abcdefghijk',
            scope=scope,
        )

        token.id_token = id_token_dic
        token.save()

        return token

    def test_oidc_login_hook(self):
        '''
        OIDC login hook should be called called when someone performs a Login through the OIDC functionalities.
        '''
        with patch('kubeportal.security.oidc_login_hook') as mocked_oidc_login_hook:
            response = self._authenticate()
            self.assertTrue(
                response['Location'].startswith(self.client.default_redirect_uri),
                msg='Different redirect_uri returned')
            self.assertTrue(response.status_code, 302)
            mocked_oidc_login_hook.assert_called()

    def test_oidc_allowed(self):
        self.app = WebApplication(name="Fancy chat tool", oidc_client=self.client)
        self.app.save()
        self.group = Group(name="Users for chat only")
        self.group.save()
        self.group.members.add(self.admin)
        self.group.web_applications.add(self.app)
        self.group.save()
        response = self._authenticate()
        self.assertTrue(response.status_code, 302)

    def test_oidc_users_group_not_for_app(self):
        self.app = WebApplication(name="Fancy chat tool", oidc_client=self.client)
        self.app.save()
        self.group = Group(name="Users for chat only")
        self.group.save()
        self.group.web_applications.add(self.app)
        self.group.save()
        with self.assertRaises(PermissionDenied):
            self._authenticate()

