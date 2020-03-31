from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.test import TestCase, client, override_settings, RequestFactory
from django.urls import reverse
from kubeportal import kubernetes, models
from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount, WebApplication, PortalGroup
from oidc_provider.lib.utils.token import create_token, create_id_token
from oidc_provider.models import Client, ResponseType
from oidc_provider.views import userinfo, AuthorizeView
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import patch
from urllib.parse import urlencode
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
        super().setUp()
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
        self.admin_group = models.PortalGroup(name="Admins", can_admin=True)
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

    @override_settings(AUTH_AD_DOMAIN='example.com')
    def test_index_view_ad_status_available(self):
        with patch('kubeportal.social.ad.is_available', return_value=True):
            response = self.c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('available', str(response.content))

    @override_settings(AUTH_AD_DOMAIN='example.com')
    def test_index_view_ad_status_unavailable(self):
        with patch('kubeportal.social.ad.is_available', return_value=False):
            response = self.c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('unavailable', str(response.content))

    @override_settings(AUTH_AD_DOMAIN=None)
    def test_index_view_ad_not_given(self):
        response = self.c.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no authentication method', str(response.content))

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)

    def test_django_secret_generation(self):
        with patch('os.path.isfile', return_value=False):
            response = self.c.get('/stats/')
            self.assertEqual(response.status_code, 302)


class FrontendLoggedInApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is approved for cluster access.
    '''

    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")
        self.c.get(reverse('admin:sync'))
        default_ns = KubernetesNamespace.objects.get(name='default')
        self.admin.service_account = default_ns.service_accounts.get(
            name='default')
        self.admin.save()

    def test_welcome_view(self):
        response = self.c.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_webapp_user_not_in_group(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        response = self.c.get('/welcome/')
        # User is not in a group that has this web app enabled
        self.assertNotContains(response, "http://www.heise.de")

    def test_webapp_user_in_group(self):
        app1 = WebApplication(name="app1", link_show=True, link_name="app1", link_url="http://www.heise.de")
        app1.save()
        group = PortalGroup()
        group.save()
        self.admin.portal_groups.add(group)
        response = self.c.get('/welcome/')
        # User is in group, but this group has the web app not enabled
        self.assertNotContains(response, "http://www.heise.de")

        group.can_web_applications.add(app1)
        response = self.c.get('/welcome/')
        # User is now in a group that has this web app enabled
        self.assertContains(response, "http://www.heise.de")

        app1.link_show = False
        app1.save()
        response = self.c.get('/welcome/')
        # User is now in a group that has this web app, but disabled
        self.assertNotContains(response, "http://www.heise.de")

    def test_config_view(self):
        response = self.c.get(reverse('config'))
        self.assertEqual(response.status_code, 200)

    def test_config_download_view(self):
        response = self.c.get(reverse('config_download'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.c.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def test_stats_with_broken_k8s_view(self):
        with patch('kubeportal.kubernetes._load_config'):
            response = self.c.get('/stats/')
            self.assertEqual(response.status_code, 200)

    def test_subauth_view_not_enabled(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 401)

    def test_subauth_view_enabled(self):
        self.admin_group.can_subauth = True
        self.admin_group.save()
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 200)

    def test_subauth_view_enabled_k8s_unavailable(self):
        self.admin_group.can_subauth = True
        self.admin_group.save()
        with patch('kubeportal.kubernetes._load_config', return_value=(None, None)):
            response = self.c.get('/subauthreq/')
            self.assertEqual(response.status_code, 401)


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

    def test_acess_request_view_mail_broken(self):
        with patch('kubeportal.models.User.send_access_request', return_value=False):
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

    def _create_group(self, name, member=None, app=None, auto_add_new=False):
        group = PortalGroup(name=name, auto_add_new=auto_add_new)
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

    def test_no_group_auto_add_new_on_deny(self):
        auto_group = self._create_group(
            name="Auto-add group", auto_add_new=True)
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

    def _call_sync(self):
        response = self.c.get(reverse('admin:sync'))
        self.assertRedirects(response, reverse('admin:index'))

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        os.system("(minikube status | grep Running) || minikube start")

    def test_kube_sync_view(self):
        self._call_sync()

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
        self._call_sync()
        ns_names = [ns.metadata.name for ns in kubernetes.get_namespaces()]
        self.assertIn("foo", ns_names)

    def test_new_external_ns_sync(self):
        self._call_sync()
        core_v1, rbac_v1 = kubernetes._load_config()
        kubernetes._create_k8s_ns("new-external-ns", core_v1)
        try:
            self._call_sync()
            new_ns_object = KubernetesNamespace.objects.get(
                name="new-external-ns")
            self.assertEqual(new_ns_object.is_synced(), True)
            for svc_account in new_ns_object.service_accounts.all():
                self.assertEqual(svc_account.is_synced(), True)
        finally:
            kubernetes._delete_k8s_ns("new-external-ns", core_v1)

    def test_new_svc_sync(self):
        self._call_sync()
        default_ns = KubernetesNamespace.objects.get(name="default")
        new_svc = KubernetesServiceAccount(name="foobar", namespace=default_ns)
        new_svc.save()
        self._call_sync()
        svc_names = [
            svc.metadata.name for svc in kubernetes.get_service_accounts()]
        self.assertIn("foobar", svc_names)

    def test_admin_index_view(self):
        response = self.c.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_k8s_sync_error_no_crash(self):
        with patch('kubeportal.kubernetes._load_config', return_value=(None, None)):
            # K8S login mocked away, view should not crash
            self._call_sync()

    def test_auto_add_approved(self):
        # Creating an auto_add_approved group should not change its member list.
        group = models.PortalGroup(
            name="Approved users", auto_add_approved=True)
        group.save()
        self.assertEquals(group.members.count(), 0)
        # Create a new user should not change the member list
        User = get_user_model()
        u = User(username="Hugo", email="a@b.de")
        u.save()
        self.assertEquals(group.members.count(), 0)
        # walk through approval workflow
        url = reverse('welcome')
        request = self.factory.get(url)
        u.send_access_request(request)
        u.save()
        # Just sending an approval request should not change to member list
        self.assertEquals(group.members.count(), 0)
        # Build full-fledged request object for logged-in admin
        url = reverse('admin:index')
        request = self.factory.get(url)
        request.user = self.admin
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Prepare K8S namespace
        ns = KubernetesNamespace(name="default")
        ns.save()
        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        # Perform approval
        assert(u.approve(request, new_svc))
        u.save()
        # Should lead to addition of user to the add_approved group
        self.assertEquals(group.members.count(), 1)

    def test_user_rejection(self):
        User = get_user_model()
        u = User(username="Hugo", email="a@b.de")
        u.save()
        # walk through rejection workflow
        url = reverse('welcome')
        request = self.factory.get(url)
        u.send_access_request(request)
        u.save()
        # Build full-fledged request object for logged-in admin
        url = reverse('admin:index')
        request = self.factory.get(url)
        request.user = self.admin
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Perform rejection
        assert(u.reject(request))
        u.save()
        assert(u.has_access_rejected())


class PortalGroups(AnonymousTestCase):
    '''
    Test cases for group functionality.
    '''

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.second_user = User(username="Fred")
        self.second_user.save()
        self.assertEquals(self.second_user.is_staff, False)

    def test_model_methods(self):
        admin_group = models.PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        admin_group.members.add(self.second_user)
        self.assertEquals(admin_group.has_member(self.second_user), True)

    def test_admin_attrib_modification_with_members(self):
        future_admin_group = models.PortalGroup(name="Admins", can_admin=False)
        future_admin_group.save()
        future_admin_group.members.add(self.second_user)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, False)
        future_admin_group.can_admin = True
        future_admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, True)
        future_admin_group.can_admin = False
        future_admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, False)

    def test_admin_attrib_add_remove_user(self):
        # Create admin group
        admin_group = models.PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        # Non-member should not become admin
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, False)
        # make member, should become admin
        admin_group.members.add(self.second_user)
        admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, True)
        # remove again from group, shopuld lose admin status
        admin_group.members.remove(self.second_user)
        admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, False)

    def test_admin_attrib_multiple(self):
        # create two admin groups
        admin_group1 = models.PortalGroup(name="Admins1", can_admin=True)
        admin_group1.save()
        admin_group2 = models.PortalGroup(name="Admins2", can_admin=True)
        admin_group2.save()
        # add same person to both groups
        admin_group1.members.add(self.second_user)
        admin_group2.members.add(self.second_user)
        admin_group1.save()
        admin_group2.save()
        # person should be admin now
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, True)
        # remove from first group, should still be admin
        admin_group1.members.remove(self.second_user)
        admin_group1.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, True)
        # remove from second group, should lose admin status
        admin_group2.members.remove(self.second_user)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_staff, False)

    def test_auto_add_new(self):
        # Creating an auto_add_new group should not change its member list.
        group = models.PortalGroup(name="All users", auto_add_new=True)
        group.save()
        self.assertEquals(group.members.count(), 0)
        # Changing an existing user should not change its member list.
        self.second_user.is_staff = not self.second_user.is_staff
        self.second_user.save()
        self.assertEquals(group.members.count(), 0)
        # Adding a new user chould change the member list
        User = get_user_model()
        self.third_admin = User(username="Hugo")
        self.third_admin.save()
        self.assertEquals(group.members.count(), 1)

    def test_forward_relation_change(self):
        '''
        Test the case that a user get her groups changed, not the other way around.
        '''
        admin_group = models.PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        self.assertEquals(admin_group.members.count(), 0)
        self.assertEquals(self.second_user.is_staff, False)
        self.second_user.portal_groups.add(admin_group)
        self.second_user.save()
        self.assertEquals(admin_group.members.count(), 1)
        self.assertEquals(self.second_user.is_staff, True)

    def test_dont_touch_superuser(self):
        '''
        The can_admin signal handler magic should not be applied to superusers,
        otherwise they may loose the backend access when not
        be a member of an admin group.
        '''
        self.second_user.is_superuser = True
        self.second_user.is_staff = True
        self.second_user.username = "NewNameToTriggerSignalHandler"
        self.second_user.save()
        self.assertEquals(self.second_user.is_superuser, True)
        self.assertEquals(self.second_user.is_staff, True)
        non_admin_group = models.PortalGroup(
            name="NonAdmins", can_admin=False)
        non_admin_group.save()
        self.second_user.portal_groups.add(non_admin_group)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEquals(self.second_user.is_superuser, True)
        self.assertEquals(self.second_user.is_staff, True)
