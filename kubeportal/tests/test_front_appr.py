import os
from django.urls import reverse

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.tests import AdminLoggedInTestCase
from unittest.mock import patch


class FrontendLoggedInApproved(AdminLoggedInTestCase):
    '''
    Tests for frontend functionality when admin is logged in,
    and she is approved for cluster access.
    '''

    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")
        self.client.get(reverse('admin:sync'))
        default_ns = KubernetesNamespace.objects.get(name='default')
        self.admin.service_account = default_ns.service_accounts.get(
            name='default')
        self.admin.save()

    def test_welcome_view(self):
        response = self.client.get('/welcome/')
        self.assertEqual(response.status_code, 200)

    def test_config_view(self):
        response = self.client.get(reverse('config'))
        self.assertEqual(response.status_code, 200)

    def test_config_download_view(self):
        response = self.client.get(reverse('config_download'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)

    def _prepare_subauth_test(self, user_in_group1, user_in_group2, app_in_group1, app_in_group2, app_enabled):
        group1 = PortalGroup()
        group1.save()
        if user_in_group1:
            self.admin.portal_groups.add(group1)

        group2 = PortalGroup()
        group2.save()
        if user_in_group2:
            self.admin.portal_groups.add(group2)

        app1 = WebApplication(name="app1", can_subauth=app_enabled)
        app1.save()

        if app_in_group1:
            group1.can_web_applications.add(app1)

        if app_in_group2:
            group2.can_web_applications.add(app1)

        return self.client.get('/subauthreq/{}/'.format(app1.pk))

    def test_subauth_invalid_cases(self):
        # Constellations for group membership of user and app
        # The expected result value assumes that the app is enabled
        cases = (
            # User is in both groups
            ((True, True, False, False), 401),
            ((True, True, True, False), 200),
            ((True, True, False, True), 200),
            ((True, True, True, True), 200),
            # User is in one of the) groups
            ((True, False, False, False), 401),
            ((True, False, True, False), 200),
            ((True, False, False, True), 401),
            ((True, False, True, True), 200),
            # User is in none of the) groups
            ((False, False, False, False), 401),
            ((False, False, True, False), 401),
            ((False, False, False, True), 401),
            ((False, False, True, True), 401),
        )
        for case, expected in cases:
            with self.subTest(case=case, expected=expected):
                response = self._prepare_subauth_test(*case, True)
                self.assertEqual(response.status_code, expected)

        # When the app is disabled, sub-auth should never succeed
        for case, expected in cases:
            with self.subTest(case=case):
                response = self._prepare_subauth_test(*case, False)
                self.assertEqual(response.status_code, 401)

    def test_subauth_k8s_broken(self):
        from kubeportal.k8s import kubernetes_api as api
        core_v1_temp, rbac_v1_temp = api.core_v1, api.rbac_v1
        api.core_v1 = None
        api.rbac_v1 = None
        self.admin_group.can_subauth = True
        self.admin_group.save()
        response = self._prepare_subauth_test(True, True, True, True, True)
        self.assertEqual(response.status_code, 401)
        api.core_v1, api.rbac_v1 = core_v1_temp, rbac_v1_temp
