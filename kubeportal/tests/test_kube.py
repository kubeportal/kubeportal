from . import AdminLoggedInTestCase
from django.urls import reverse
from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount
from kubeportal import kubernetes
import os


class FrontendLoggedInApproved(AdminLoggedInTestCase):

    def setUp(self):
        super().setUp()
        os.system("(minikube status | grep Running) || minikube start")
        response = self.c.get(reverse('admin:sync'))
        self.assertEqual(response.status_code, 200)
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

    def test_subauth_view(self):
        response = self.c.get('/subauthreq/')
        self.assertEqual(response.status_code, 200)


class Backend(AdminLoggedInTestCase):

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
            self.assertEqual(KubernetesNamespace.objects.filter(name="new-external-ns").count(), 1)
        finally:
            kubernetes._delete_k8s_ns("new-external-ns", core_v1)

    def test_new_svc_sync(self):
        self.c.get(reverse('admin:sync'))
        default_ns = KubernetesNamespace.objects.get(name="default")
        new_svc = KubernetesServiceAccount(name="foobar", namespace=default_ns)
        new_svc.save()
        self.c.get(reverse('admin:sync'))
