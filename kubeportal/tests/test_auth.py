'''
    Test code for authentication-related code parts.

    Most parts are copied from https://github.com/juanifioren/django-oidc-provider/tree/master/oidc_provider/tests.
'''

from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from oidc_provider.views import userinfo
from oidc_provider.models import Client, ResponseType
from oidc_provider.lib.utils.token import create_token, create_id_token
from . import AdminLoggedOutTestCase, admin_data
import uuid
import random
import json


class FrontendAuth(AdminLoggedOutTestCase):

    def _create_token(self, request):
        scope = ['openid', 'email']

        token = create_token(
            user=self.admin,
            client=self.client,
            scope=scope)

        id_token_dic = create_id_token(
            token=token,
            user=self.admin,
            aud=self.client.client_id,
            nonce='cb584e44c43ed6bd0bc2d9c7e242837d',
            scope=scope,
            request=request
        )

        token.id_token = id_token_dic
        token.save()

        return token

    def setUp(self):
        super().setUp()
        call_command('creatersakey')
        self.factory = RequestFactory()
        self.client = Client()
        self.client.name = 'Some Client'
        self.client.client_id = str(random.randint(1, 999999)).zfill(6)
        self.client.client_secret = str(random.randint(1, 999999)).zfill(6)
        self.client.redirect_uris = ['http://example.com/']
        self.client.require_consent = True
        self.client.save()
        self.client.response_types.add(ResponseType.objects.get(value='code'))
        self.state = uuid.uuid4().hex
        self.nonce = uuid.uuid4().hex

    def test_userinfo(self):
        '''
            Simulates that the OIDC client application is fetching user information.
        '''
        url = reverse('oidc_provider:userinfo')

        request = self.factory.post(url, data={}, content_type='multipart/form-data')
        token = self._create_token(request)
        request.META['HTTP_AUTHORIZATION'] = 'Bearer ' + token.access_token
        response = userinfo(request)
        self.assertEquals(json.loads(response.content)['email'], admin_data['email'])
