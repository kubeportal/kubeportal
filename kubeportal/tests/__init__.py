from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import TestCase, client, override_settings, RequestFactory
from django.urls import reverse
from django.utils import timezone
from kubeportal import kubernetes, models
from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount, WebApplication, PortalGroup
from kubeportal.views import WelcomeView
from oidc_provider.lib.utils.token import create_token, create_id_token
from oidc_provider.models import Client, ResponseType, Token
from oidc_provider.views import userinfo, TokenIntrospectionView, AuthorizeView
from unittest.mock import patch
from urllib.parse import urlencode
import json
import logging
import os
import random
import uuid

logging.getLogger('KubePortal').setLevel(logging.DEBUG)
logging.getLogger('django.request').setLevel(logging.DEBUG)
logging.getLogger('social').setLevel(logging.DEBUG)

admin_clear_password = 'adminäö&%/1`'

admin_data = {
    'username': 'adminäö&%/1`',
    'email': 'adminäö&%/1`@example.com',
    'password': make_password(admin_clear_password),
    'is_staff': True,
    'is_superuser': True
}


class BaseTestCase(TestCase):
    '''
    Nobody is logged in. No user is prepared.
    '''

    def setUp(self):
        self.c = client.Client()


class AnonymousTestCase(BaseTestCase):
    '''
    Nobody is logged in. No user is prepared.
    '''

    def setUp(self):
        super().setUp()


class AdminLoggedOutTestCase(BaseTestCase):
    '''
    An administrator is logged out and part of an auto-admin group.
    Web applications and subauth's are not enabled.
    '''

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.admin = User(**admin_data)
        self.admin.save()
        self.admin_group = models.PortalGroup(name="Admins", auto_admin=True)
        self.admin_group.save()
        self.admin_group.members.add(self.admin)
        self.admin_group.save()


class AdminLoggedInTestCase(AdminLoggedOutTestCase):
    '''
    An administrator is logged in and part of an auto-admin group.
    Web applications and subauth's are not enabled.
    '''

    def login_admin(self):
        self.c.login(username=admin_data['username'],
                     password=admin_clear_password)

    def setUp(self):
        super().setUp()
        self.login_admin()


class FrontendAnonymous(AnonymousTestCase):
    '''
    Tests for frontend functionality when nobody is logged in.
    '''
    def test_index_view(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)


class FrontendLoggedInApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is approved for cluster access.
    '''
    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")
        response = self.c.get(reverse('admin:sync'))
        default_ns = KubernetesNamespace.objects.get(name='default')
        self.admin.service_account = default_ns.service_accounts.get(
            name='default')
        self.admin.save()

    def test_welcome_view(self):
        response = self.c.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_config_view(self):
        response = self.c.get(reverse('config'))
        self.assertEqual(response.status_code, 200)

    def test_config_download_view(self):
        response = self.c.get(reverse('config_download'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.c.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_subauth_view_not_enabled(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)

    def test_subauth_view_enabled(self):
        self.admin_group.subauth = True
        self.admin_group.save()
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 200)


class FrontendLoggedInNotApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is NOT approved for cluster access.
    '''
    def test_index_view(self):
        # User is already logged in, expecting welcome redirect
        response = self.c.get('/')
        self.assertEqual(response.status_code, 302)

    def test_welcome_view(self):
        response = self.c.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_config_view(self):
        response = self.c.get(reverse('config'))
        self.assertEqual(response.status_code, 403)

    def test_config_download_view(self):
        response = self.c.get(reverse('config_download'))
        self.assertEqual(response.status_code, 403)

    def test_stats_view(self):
        response = self.c.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_root_redirect_with_next_param(self):
        response = self.c.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_root_redirect_with_rd_param(self):
        response = self.c.get('/?next=/config')
        self.assertEqual(response.status_code, 302)

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)

    def test_logout_view(self):
        # User is already logged in, expecting redirect
        response = self.c.get('/logout/')
        self.assertEqual(response.status_code, 302)

    def test_acess_request_view(self):
        response = self.c.get('/access/request/')
        self.assertRedirects(response, '/welcome/')


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
            self.app[index] = WebApplication(
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

    def _create_group(self, name, member=None, app=None, auto_add=False):
        group = PortalGroup(name=name, auto_add=auto_add)
        group.save()
        if member:
            group.members.add(member)
        if app:
            group.web_applications.add(app)
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
        group1 = self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[0])
        group2 = self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        response = self._authenticate(self.client[0])
        self.assertTrue(response.status_code, 302)
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[1])

    def test_multiple_groups_multiple_allowed(self):
        group1 = self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[0])
        group2 = self._create_group(
            name="Users for chat only", member=self.admin, app=self.app[1])
        response = self._authenticate(self.client[0])
        self.assertTrue(response.status_code, 302)
        response = self._authenticate(self.client[1])
        self.assertTrue(response.status_code, 302)

    def test_multiple_groups_none_allowed(self):
        group1 = self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        group2 = self._create_group(
            name="Users for chat only", member=self.admin, app=None)
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[0])
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[1])

    def test_no_group_auto_add_on_deny(self):
        auto_group = self._create_group(
            name="Auto-add group", auto_add=True)
        with self.assertRaises(PermissionDenied):
            self._authenticate(self.client[0])
        self.assertEquals(auto_group.members.all().count(), 0)

    def test_token_auth(self):
        url = reverse('oidc_provider:userinfo')
        request = self.factory.post(
            url, data={}, content_type='multipart/form-data')
        token = self._create_token(self.admin, self.client[0], request)
        request.META['HTTP_AUTHORIZATION'] = 'Bearer {0}'.format(
            token.access_token)
        response = userinfo(request)
        self.assertTrue(response.status_code, 200)


class Backend(AdminLoggedInTestCase):
    '''
    Tests for backend functionality when admin is logged in.
     '''
    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")

    def test_kube_sync_view(self):
        response = self.c.get(reverse('admin:sync'))
        self.assertRedirects(response, reverse('admin:index'))

    def test_kube_ns_changelist(self):
        response = self.c.get(
            reverse('admin:kubeportal_kubernetesnamespace_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_kube_svc_changelist(self):
        response = self.c.get(
            reverse('admin:kubeportal_kubernetesserviceaccount_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_user_changelist(self):
        response = self.c.get(reverse('admin:kubeportal_user_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_new_ns_sync(self):
        new_ns = KubernetesNamespace(name="foo")
        new_ns.save()
        self.c.get(reverse('admin:sync'))
        ns_names = [ns.metadata.name for ns in kubernetes.get_namespaces()]
        self.assertIn("foo", ns_names)

    def test_new_external_ns_sync(self):
        self.c.get(reverse('admin:sync'))
        core_v1, rbac_v1 = kubernetes._load_config()
        kubernetes._create_k8s_ns("new-external-ns", core_v1)
        try:
            self.c.get(reverse('admin:sync'))
            self.assertEqual(KubernetesNamespace.objects.filter(
                name="new-external-ns").count(), 1)
        finally:
            kubernetes._delete_k8s_ns("new-external-ns", core_v1)

    def test_new_svc_sync(self):
        self.c.get(reverse('admin:sync'))
        default_ns = KubernetesNamespace.objects.get(name="default")
        new_svc = KubernetesServiceAccount(name="foobar", namespace=default_ns)
        new_svc.save()
        self.c.get(reverse('admin:sync'))

    def test_admin_index_view(self):
        response = self.c.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def k8s_sync_error(self):
        response = self.c.get(reverse('admin:sync'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'my message')


class PortalGroups(AnonymousTestCase):
    '''
    Test cases for group functionality.
    '''
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.second_admin = User(username="Fred")
        self.second_admin.save()
        self.assertEquals(self.second_admin.is_staff, False)

    def test_post_save_group_members(self):
        '''
        Make sure that the signal handler is called.
        '''
        admin_group = models.PortalGroup(name="Admins", auto_admin=True)
        # Note: We cannot patch the original signal handler:
        # https://stackoverflow.com/questions/13112302/how-do-i-mock-a-django-signal-handler
        with patch('kubeportal.signals._set_staff_status') as mocked_handle_group_change:
            admin_group.save()
            mocked_handle_group_change.assert_not_called()
            admin_group.members.add(self.second_admin)
            admin_group.save()
            mocked_handle_group_change.assert_called()

    def test_auto_admin_add_remove_user(self):
        # Create admin group
        admin_group = models.PortalGroup(name="Admins", auto_admin=True)
        admin_group.save()
        # Non-member should not become admin
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, False)
        # make member, should become admin
        admin_group.members.add(self.second_admin)
        admin_group.save()
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, True)
        # remove again from group, shopuld lose admin status
        admin_group.members.remove(self.second_admin)
        admin_group.save()
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, False)

    def test_two_auto_admin_groups(self):
        # create two admin groups
        admin_group1 = models.PortalGroup(name="Admins1", auto_admin=True)
        admin_group1.save()
        admin_group2 = models.PortalGroup(name="Admins2", auto_admin=True)
        admin_group2.save()
        # add same person to both groups
        admin_group1.members.add(self.second_admin)
        admin_group2.members.add(self.second_admin)
        admin_group1.save()
        admin_group2.save()
        # person should be admin now
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, True)
        # remove from first group, should still be admin
        admin_group1.members.remove(self.second_admin)
        admin_group1.save()
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, True)
        # remove from second group, should lose admin status
        admin_group2.members.remove(self.second_admin)
        self.second_admin.refresh_from_db() # catch changes from signal handlers
        self.assertEquals(self.second_admin.is_staff, False)

    def test_auto_add_group(self):
        # Creating an auto_add group should not change its member list.
        group = models.PortalGroup(name="All users", auto_add=True)
        group.save()
        self.assertEquals(group.members.count(), 0)
        # Changing an existing user should not change its member list.
        self.second_admin.is_staff=not self.second_admin.is_staff
        self.second_admin.save()
        self.assertEquals(group.members.count(), 0)
        # Adding a new user chould change the member list
        User = get_user_model()
        self.third_admin = User(username="Hugo")
        self.third_admin.save()
        self.assertEquals(group.members.count(), 1)

    def test_forward_relation_change(self):
        admin_group = models.PortalGroup(name="Admins", auto_admin=True)
        admin_group.save()
        self.assertEquals(admin_group.members.count(), 0)
        self.second_admin.portal_groups.add(admin_group)
        self.second_admin.save()
        self.assertEquals(admin_group.members.count(), 1)

