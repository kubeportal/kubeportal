import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.test import client
from django.urls import reverse

from kubeportal.k8s import k8s_sync
from kubeportal.k8s.utils import is_minikube
from kubeportal.models.portalgroup import PortalGroup

logging.getLogger('KubePortal').setLevel(logging.DEBUG)
logging.getLogger('django.request').setLevel(logging.WARNING)
logging.getLogger('django').setLevel(logging.WARNING)

admin_clear_password = 'adminäö&%/1`'

admin_data = {
    'first_name': 'Peter',
    'last_name': 'Admin',
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

    admin_group_name = 'Admins'

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client = client.Client()
        assert(is_minikube())

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

    def _build_full_post_request_mock(self, short_url, data):
        url = reverse(short_url)
        request = self.factory.post(url, data)
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
        sync_success = k8s_sync.sync(request)
        self.assertEqual(sync_success, expect_success)


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
        self.admin_group = PortalGroup(name=self.admin_group_name, can_admin=True)
        self.admin_group.save()
        self.admin_group.members.add(self.admin)
        self.admin_group.save()


class AdminLoggedInTestCase(AdminLoggedOutTestCase):
    '''
    An administrator is logged in and part of an auto-admin group.
    Web applications and subauth's are not enabled.
    '''

    def login_admin(self):
        self.client.login(username=admin_data['username'],
                     password=admin_clear_password)

    def setUp(self):
        super().setUp()
        self.login_admin()
