import os

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test import override_settings
from django.urls import reverse
from kubeportal import kubernetes
from kubeportal import models
from kubeportal.models import KubernetesNamespace
from kubeportal.models import KubernetesServiceAccount
from kubeportal.models import PortalGroup
from kubeportal.tests import AdminLoggedInTestCase
from unittest.mock import patch
from kubeportal.admin import merge_users, UserAdmin


class Backend(AdminLoggedInTestCase):
    '''
    Tests for backend functionality when admin is logged in.
     '''

    def _build_full_request_mock(self, short_url):
        url = reverse(short_url)
        request = self.factory.get(url)
        request.user = self.admin
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def _call_sync(self, expect_success=True):
        # We are calling the sync method directly here, and not through the view,
        # so that the result of sync is directly analyzed
        request = self._build_full_request_mock('admin:index')
        sync_success = kubernetes.sync(request)
        self.assertEquals(sync_success, expect_success)

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        os.system("(minikube status | grep Running) || minikube start")

    def test_kube_ns_changelist(self):
        self._call_sync()
        response = self.c.get(
            reverse('admin:kubeportal_kubernetesnamespace_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_kube_svc_changelist(self):
        self._call_sync()
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

    def test_new_ns_broken_name_sync(self):
        core_v1, rbac_v1 = kubernetes._load_config()
        new_ns = KubernetesNamespace(name="foo_bar")
        new_ns.save()
        self._call_sync()
        ns_names = [ns.metadata.name for ns in kubernetes.get_namespaces()]
        self.assertNotIn("foo_bar", ns_names)
        self.assertIn("foobar", ns_names)
        self.assertEquals(KubernetesNamespace.objects.filter(name="foobar").exists(), True)
        kubernetes._delete_k8s_ns("foobar", core_v1)

    def test_new_external_ns_sync(self):
        self._call_sync()
        core_v1, rbac_v1 = kubernetes._load_config()
        kubernetes._create_k8s_ns("new-external-ns1", core_v1)
        try:
            self._call_sync()
            new_ns_object = KubernetesNamespace.objects.get(
                name="new-external-ns1")
            self.assertEqual(new_ns_object.is_synced(), True)
            for svc_account in new_ns_object.service_accounts.all():
                self.assertEqual(svc_account.is_synced(), True)
        finally:
            kubernetes._delete_k8s_ns("new-external-ns1", core_v1)

    def test_exists_both_sides_sync(self):
        self._call_sync()
        core_v1, rbac_v1 = kubernetes._load_config()
        kubernetes._create_k8s_ns("new-external-ns2", core_v1)
        new_ns = KubernetesNamespace(name="new-external-ns2")
        new_ns.save()
        try:
            self._call_sync()
        finally:
            kubernetes._delete_k8s_ns("new-external-ns2", core_v1)

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

    def test_special_k8s_approved(self):
        # Creating an auto_add_approved group should not change its member list.
        group = models.PortalGroup.objects.get(special_k8s_accounts=True)
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
        request = self._build_full_request_mock('admin:index')
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


    def test_special_k8s_unapproved(self):
        group = models.PortalGroup.objects.get(special_k8s_accounts=True)
        ns = KubernetesNamespace(name="default")
        ns.save()
        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        User = get_user_model()
        # create approved user
        u = User(username="Hugo",
                 email="a@b.de",
                 state=models.UserState.ACCESS_APPROVED,
                 service_account = new_svc)
        u.save()
        self.assertEquals(group.members.count(), 1)
        # unapprove
        u.state=models.UserState.ACCESS_REJECTED
        u.save()
        self.assertEquals(group.members.count(), 0)


    def _test_user_rejection(self):
        User = get_user_model()
        u = User(username="Hugo", email="a@b.de")
        u.save()
        # walk through rejection workflow
        url = reverse('welcome')
        request = self.factory.get(url)
        u.send_access_request(request)
        u.save()
        # Build full-fledged request object for logged-in admin
        request = self._build_full_request_mock('admin:index')
        assert(u.reject(request))
        u.save()
        assert(u.has_access_rejected())

    def test_user_rejection(self):
        self._test_user_rejection()

    '''
    Create two users with the secondary (the later created) one having cluster access,
    an assigned comment and two assigned groups
    Merge both users.
    The primary user should be assigned the cluster access, user comment and all the
    portal groups of the secondary user.
    The secondary user should be deleted.
    '''
    def test_user_merge_access_approved(self):
        User = get_user_model()
        primary = User(
                username="HUGO",
                email="a@b.de")
        primary.save()

        ns = KubernetesNamespace(name="default")
        ns.save()
        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        secondary = User(
                username="hugo",
                state=models.UserState.ACCESS_APPROVED,
                email="a@b.de",
                comments = "secondary user comment",
                service_account = new_svc)
        secondary.save()

        group1 = PortalGroup(name="testgroup1")
        group1.save()
        group2 = PortalGroup(name="testgroup2")
        group2.save()

        secondary.portal_groups.add(group1)
        secondary.portal_groups.add(group2)
        secondary.save()

        # Build full-fledged request object for logged-in admin
        request = self._build_full_request_mock('admin:index')
        # approve secondary for cluster access
        secondary.approve(request, new_svc)

        # the merge method only accepts a queryset of users since that's what
        # the admin interface creates
        queryset_of_users = User.objects.filter(pk__in = [primary.id, secondary.id])

        # merge both users. shouldn't return anything
        assert(not merge_users(UserAdmin, request, queryset_of_users))

        # the primary user has been altered but the old object is still in memory
        # we need to query for the updated user again
        primary = User.objects.get(pk = primary.id)

        # Does primary have all the values of secondary user?
        self.assertEquals(primary.comments, "secondary user comment")
        assert(primary.portal_groups.filter(name = group1.name))
        assert(primary.portal_groups.filter(name = group2.name))
        assert(primary.has_access_approved)

    '''
    Create two users with the secondary (the later created) one having rejected cluster access,
    Merge both users.
    The primary user should be assigned the rejected cluster access.
    The secondary user should be deleted.
    '''
    def test_user_merge_access_rejected(self):
        User = get_user_model()
        primary = User(
                username="HUGO",
                email="a@b.de")
        primary.save()

        ns = KubernetesNamespace(name="default")
        ns.save()
        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        secondary = User(
                username="hugo",
                state=models.UserState.ACCESS_APPROVED,
                email="a@b.de",
                comments = "secondary user comment",
                service_account = new_svc)
        secondary.save()

        # Build full-fledged request object for logged-in admin
        request = self._build_full_request_mock('admin:index')
        # reject cluster access for secondary
        secondary.reject(request)

        # the merge method only accepts a queryset of users since that's what
        # the admin interface creates
        queryset_of_users = User.objects.filter(pk__in = [primary.id, secondary.id])

        # merge both users. shouldn't return anything
        assert(not merge_users(UserAdmin, request, queryset_of_users))

        # the primary user has been altered but the old object is still in memory
        # we need to query for the updated user again
        primary = User.objects.get(pk = primary.id)

        assert(primary.has_access_rejected)


    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST_PASSWORD='sdsds')
    def test_user_rejection_mail_broken(self):
        self._test_user_rejection()
