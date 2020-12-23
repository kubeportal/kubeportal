import os
from unittest import skip
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse

from kubeportal.admin import merge_users, UserAdmin
from kubeportal.admin_views import prune
from kubeportal.k8s import kubernetes_api as api
from kubeportal.models import UserState
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.tests import AdminLoggedInTestCase


class Backend(AdminLoggedInTestCase):
    '''
    Tests for backend functionality when admin is logged in.
    '''

    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")

    def test_kube_ns_changelist(self):
        self._call_sync()
        response = self.client.get(
            reverse('admin:kubeportal_kubernetesnamespace_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_kube_svc_changelist(self):
        self._call_sync()
        response = self.client.get(
            reverse('admin:kubeportal_kubernetesserviceaccount_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_user_changelist(self):
        response = self.client.get(reverse('admin:kubeportal_user_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_new_ns_sync(self):
        new_ns = KubernetesNamespace(name="foo")
        new_ns.save()
        self._call_sync()
        ns_names = [ns.metadata.name for ns in api.get_namespaces()]
        self.assertIn("foo", ns_names)

    def test_new_ns_broken_name_sync(self):
        test_cases = {"foo_bar": "foobar", "ABCDEF": "abcdef"}
        for old, new in test_cases.items():
            new_ns = KubernetesNamespace(name=old)
            new_ns.save()
            self._call_sync()
            ns_names = [ns.metadata.name for ns in api.get_namespaces()]
            self.assertNotIn(old, ns_names)
            self.assertIn(new, ns_names)

    def test_new_external_ns_sync(self):
        self._call_sync()
        api.create_k8s_ns("new-external-ns1")
        try:
            self._call_sync()
            new_ns_object = KubernetesNamespace.objects.get(
                name="new-external-ns1")
            self.assertEqual(new_ns_object.is_synced(), True)
            for svc_account in new_ns_object.service_accounts.all():
                self.assertEqual(svc_account.is_synced(), True)
        finally:
            api.delete_k8s_ns("new-external-ns1")

    def test_exists_both_sides_sync(self):
        self._call_sync()
        api.create_k8s_ns("new-external-ns2")
        new_ns = KubernetesNamespace(name="new-external-ns2")
        new_ns.save()
        try:
            self._call_sync()
        finally:
            api.delete_k8s_ns("new-external-ns2")

    def test_new_svc_sync(self):
        self._call_sync()
        default_ns = KubernetesNamespace.objects.get(name="default")
        new_svc = KubernetesServiceAccount(name="foobar", namespace=default_ns)
        new_svc.save()
        self._call_sync()
        svc_names = [
            svc.metadata.name for svc in api.get_service_accounts()]
        self.assertIn("foobar", svc_names)

    def test_admin_index_view(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_special_k8s_approved(self):
        # Creating an auto_add_approved group should not change its member list.
        group = PortalGroup.objects.get(special_k8s_accounts=True)
        self.assertEqual(group.members.count(), 0)
        # Create a new user should not change the member list
        User = get_user_model()
        u = User(username="Hugo", email="a@b.de")
        u.save()
        self.assertEqual(group.members.count(), 0)
        # walk through approval workflow
        url = reverse('welcome')
        request = self.factory.get(url)
        u.send_access_request(request)
        u.save()
        # Just sending an approval request should not change to member list
        self.assertEqual(group.members.count(), 0)
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
        self.assertEqual(group.members.count(), 1)

    def test_special_k8s_unapproved(self):
        group = PortalGroup.objects.get(special_k8s_accounts=True)
        ns = KubernetesNamespace(name="default")
        ns.save()
        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        User = get_user_model()
        # create approved user
        u = User(username="Hugo",
                 email="a@b.de",
                 state=UserState.ACCESS_APPROVED,
                 service_account=new_svc)
        u.save()
        self.assertEqual(group.members.count(), 1)
        # unapprove
        u.state = UserState.ACCESS_REJECTED
        u.save()
        self.assertEqual(group.members.count(), 0)

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

    def test_request_approval_specific_administrator(self):
        # Create a new user should not change the member list
        User = get_user_model()
        u = User(username="Hugo", email="a@b.de")
        u.save()
        # walk through approval workflow
        url = reverse('welcome')
        request = self.factory.get(url)
        u.send_access_request(request, self.admin.username)
        u.save()
        # Build full-fledged request object for logged-in admin
        request = self._build_full_request_mock('admin:index')
        # create service account and namespace for user

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
            state=UserState.ACCESS_APPROVED,
            email="a@b.de",
            comments="secondary user comment",
            service_account=new_svc)
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
        queryset_of_users = User.objects.filter(
            pk__in=[primary.id, secondary.id])

        # merge both users. shouldn't return anything
        assert(not merge_users(UserAdmin, request, queryset_of_users))

        # the primary user has been altered but the old object is still in memory
        # we need to query for the updated user again
        primary = User.objects.get(pk=primary.id)

        # Does primary have all the values of secondary user?
        self.assertEqual(primary.comments, "secondary user comment")
        assert(primary.portal_groups.filter(name=group1.name))
        assert(primary.portal_groups.filter(name=group2.name))
        assert(primary.has_access_approved)

    '''
    Create two users with the secondary (the later created) one having rejected cluster access,
    Merge both users.
    The primary user should be assigned the rejected cluster access.
    The secondary user should be deleted.
    '''

    def test_user_merge_access_rejected(self):
        request = self._build_full_request_mock('admin:index')

        User = get_user_model()
        primary = User(
            username="HUGO",
            email="a@b.de")
        primary.save()

        ns = KubernetesNamespace(name="default")
        ns.save()

        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        # Perform approval
        assert(primary.approve(request, new_svc))
        primary.save()

        secondary = User(
            username="hugo",
            state=UserState.ACCESS_APPROVED,
            email="a@b.de",
            comments="secondary user comment",
            service_account=new_svc)
        secondary.save()

        # Build full-fledged request object for logged-in admin
        request = self._build_full_request_mock('admin:index')
        # reject cluster access for secondary
        secondary.reject(request)

        # the merge method only accepts a queryset of users since that's what
        # the admin interface creates
        queryset_of_users = User.objects.filter(
            pk__in=[primary.id, secondary.id])

        # merge both users. shouldn't return anything
        assert(not merge_users(UserAdmin, request, queryset_of_users))

        # the primary user has been altered but the old object is still in memory
        # we need to query for the updated user again
        primary = User.objects.get(pk=primary.id)

        assert primary.has_access_rejected

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST_PASSWORD='sdsds')
    def test_user_rejection_mail_broken(self):
        self._test_user_rejection()

    @skip("Function disabled")
    def test_backend_cleanup_view(self):
        User = get_user_model()
        u = User(
            username="HUGO",
            email="a@b.de")
        u.save()

        # we need an inactive user for the the filter to work
        from dateutil.parser import parse
        u.last_login = parse("2017-09-23 11:21:52.909020")
        u.save()

        ns = KubernetesNamespace(name="aaasdfadfasdfasdf", visible=True)
        ns.save()

        new_svc = KubernetesServiceAccount(name="foobar", namespace=ns)
        new_svc.save()
        new_svc.delete()

        request = self._build_full_request_mock('admin:cleanup')
        assert(request)

    @skip("Function disabled")
    def test_backend_cleanup_entitity_getters():
        User = get_user_model()
        from django.utils import dateparse
        # we need an inactive user for the the filter to work
        u = User(
            username="HUGO",
            email="a@b.de",
            last_login=dateparse.parse_datetime(
                "2017-09-23 11:21:52.909020 +02.00")
        )
        u.save()

        ns = KubernetesNamespace(name="asdfadfasdfasdf", visible=True)
        ns.save()

        assert(User.inactive_users()[0] ==
               User.objects.get(username=u.username))
        assert(KubernetesNamespace.without_pods()[0] == ns)
        assert(KubernetesNamespace.without_service_accounts()[0] == ns)

    @skip("Function disabled")
    def test_backend_prune_view(self):
        User = get_user_model()
        from django.utils import dateparse
        # we need an inactive user for the the filter to work
        user_list = [
            User.objects.create_user(
                username="HUGO1",
                email="a@b.de",
                last_login=dateparse.parse_datetime(
                    "2017-09-23 11:21:52.909020 +02:00")
            ),

            User.objects.create_user(
                username="HUGO2",
                email="b@b.de",
                last_login=dateparse.parse_datetime(
                    "2017-09-23 11:21:52.909020 +02:00")
            ),

            User.objects.create_user(
                username="HUGO3",
                email="c@b.de",
                last_login=dateparse.parse_datetime(
                    "2017-09-23 11:21:52.909020 +02:00")
            )
        ]

        ns_list = [
            KubernetesNamespace.objects.create(name="test-namespace1"),
            KubernetesNamespace.objects.create(name="test-namespace2"),
            KubernetesNamespace.objects.create(name="test-namespace3")
        ]

        # prune visible namespaces without an assigned service account
        request = self._build_full_post_request_mock("admin:prune", {
            'prune': "namespaces-no-service-acc",
            "namespaces": [ns.name for ns in ns_list]
        })
        prune(request)

        assert(not KubernetesNamespace.objects.filter(
            name__in=[ns.name for ns in ns_list]))

        ns_list = [
            KubernetesNamespace.objects.create(name="test-namespace1"),
            KubernetesNamespace.objects.create(name="test-namespace2"),
            KubernetesNamespace.objects.create(name="test-namespace3")
        ]

        # prune visible namespaces without pods
        request = self._build_full_post_request_mock("admin:prune", {
            'prune': "namespaces-no-pods",
            "namespaces": [ns.name for ns in ns_list]
        })
        prune(request)

        # have all been pruned?
        assert(not KubernetesNamespace.objects.filter(
            name__in=[ns.name for ns in ns_list]))

        # prune service accounts that haven't logged in for a long time
        request = self._build_full_post_request_mock("admin:prune", {
            'prune': "inactive-users",
            "users": [u.username for u in user_list]
        })
        prune(request)

        # have all been pruned?
        assert(not KubernetesServiceAccount.objects.filter(
            name__in=[u.username for u in user_list]))
