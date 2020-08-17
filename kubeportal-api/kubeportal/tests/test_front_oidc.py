import random
import uuid

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse
from kubeportal.tests import AdminLoggedOutTestCase
from kubeportal import models
from oidc_provider.lib.utils.token import create_id_token
from oidc_provider.lib.utils.token import create_token
from oidc_provider.models import Client
from oidc_provider.models import ResponseType
from oidc_provider.views import AuthorizeView
from oidc_provider.views import userinfo
from unittest.mock import patch
from urllib.parse import urlencode


class FrontendOidc(AdminLoggedOutTestCase):
    '''
    Tests for frontend functionality when admin is NOT logged in,
    and she authenticates through OpenID Connect.
    '''

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client = {}
        self.app = {}
        for index, name in enumerate(["Fancy chat tool", "Fancy wiki tool"]):
            self.client[index] = Client()
            self.client[index].name = name
            self.client[index].client_id = str(
                random.randint(1, 999999)).zfill(6)
            self.client[index].client_secret = str(
                random.randint(1, 999999)).zfill(6)
            self.client[index].redirect_uris = ['http://example.com/']
            self.client[index].require_consent = False
            self.client[index].save()
            self.client[index].response_types.add(
                ResponseType.objects.get(value='code'))
            self.app[index] = models.WebApplication(
                name=name, oidc_client=self.client[index])
            self.app[index].save()
        self.state = uuid.uuid4().hex

    def _authenticate(self, client):
        data = {
            'client_id': client.client_id,
            'redirect_uri': client.default_redirect_uri,
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

    def _create_token(self, user, client, request):
        scope = ['openid', 'email']

        token = create_token(
            user=user,
            client=client,
            scope=scope)

        id_token_dic = create_id_token(
            token=token,
            user=user,
            aud=client.client_id,
            nonce='abcdefghijk',
            scope=scope,
            request=request
        )

        token.id_token = id_token_dic
        token.save()

        return token

    def _create_group(self, name, member=None, app=None):
        group = models.PortalGroup(name=name)
        group.save()
        if member:
            group.members.add(member)
        if app:
            group.can_web_applications.add(app)
        group.save()
        return group

    def test_login_hook(self):
        '''
        OIDC login hook should be called called when someone performs a Login through the OIDC functionalities.
        '''
        client = self.client[0]
        with patch('kubeportal.security.oidc_login_hook') as mocked_oidc_login_hook:
            response = self._authenticate(client)
            self.assertTrue(
                response['Location'].startswith(client.default_redirect_uri),
                msg='Different redirect_uri returned')
            self.assertTrue(response.status_code, 302)
            mocked_oidc_login_hook.assert_called()

    def test_multiple_groups_one_allowed(self):
        self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[0])
        self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        response = self._authenticate(self.client[0])
        self.assertTrue(response.status_code, 302)
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[1])

    def test_multiple_groups_multiple_allowed(self):
        self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[0])
        self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[1])
        response = self._authenticate(self.client[0])
        self.assertTrue(response.status_code, 302)
        response = self._authenticate(self.client[1])
        self.assertTrue(response.status_code, 302)

    def test_multiple_groups_none_allowed(self):
        self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[0])
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[1])

    def test_token_auth(self):
        url = reverse('oidc_provider:userinfo')
        request = self.factory.post(
            url, data={}, content_type='multipart/form-data')
        token = self._create_token(self.admin, self.client[0], request)
        request.META['HTTP_AUTHORIZATION'] = 'Bearer {0}'.format(
            token.access_token)
        response = userinfo(request)
        self.assertTrue(response.status_code, 200)
