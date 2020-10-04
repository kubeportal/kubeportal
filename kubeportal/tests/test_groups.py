from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.tests import AnonymousTestCase


class PortalGroups(AnonymousTestCase):
    """
    Test cases for group functionality.
    """

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.second_user = User(username="Fred")
        self.second_user.save()
        self.assertEqual(self.second_user.is_staff, False)

    def test_model_methods(self):
        admin_group = PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        admin_group.members.add(self.second_user)
        self.assertEqual(admin_group.has_member(self.second_user), True)

    def test_admin_attrib_modification_with_members(self):
        future_admin_group = PortalGroup(name="Admins", can_admin=False)
        future_admin_group.save()
        future_admin_group.members.add(self.second_user)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, False)
        future_admin_group.can_admin = True
        future_admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, True)
        future_admin_group.can_admin = False
        future_admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, False)

    def test_admin_attrib_add_remove_user(self):
        # Create admin group
        admin_group = PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        # Non-member should not become admin
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, False)
        # make member, should become admin
        admin_group.members.add(self.second_user)
        admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, True)
        # remove again from group, shopuld lose admin status
        admin_group.members.remove(self.second_user)
        admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, False)

    def test_admin_attrib_multiple(self):
        # create two admin groups
        admin_group1 = PortalGroup(name="Admins1", can_admin=True)
        admin_group1.save()
        admin_group2 = PortalGroup(name="Admins2", can_admin=True)
        admin_group2.save()
        # add same person to both groups
        admin_group1.members.add(self.second_user)
        admin_group2.members.add(self.second_user)
        admin_group1.save()
        admin_group2.save()
        # person should be admin now
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, True)
        # remove from first group, should still be admin
        admin_group1.members.remove(self.second_user)
        admin_group1.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, True)
        # remove from second group, should lose admin status
        admin_group2.members.remove(self.second_user)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_staff, False)

    def test_permission_adjustment(self):
        self.assertEqual(self.second_user.user_permissions.all().count(), 0)
        # Create admin group
        admin_group = PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        # make member, should get all model permissions
        admin_group.members.add(self.second_user)
        admin_group.save()
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        perm_count = Permission.objects.count()
        self.assertEqual(self.second_user.user_permissions.all().count(), perm_count)

    def test_forward_relation_change(self):
        """
        Test the case that a user get her groups changed, not the other way around.
        """
        admin_group = PortalGroup(name="Admins", can_admin=True)
        admin_group.save()
        self.assertEqual(admin_group.members.count(), 0)
        self.assertEqual(self.second_user.is_staff, False)
        self.second_user.portal_groups.add(admin_group)
        self.second_user.save()
        self.assertEqual(admin_group.members.count(), 1)
        self.assertEqual(self.second_user.is_staff, True)

    def test_dont_touch_superuser(self):
        """
        The can_admin signal handler magic should not be applied to superusers,
        otherwise they may loose the backend access when not
        be a member of an admin group.
        """
        self.second_user.is_superuser = True
        self.second_user.is_staff = True
        self.second_user.username = "NewNameToTriggerSignalHandler"
        self.second_user.save()
        self.assertEqual(self.second_user.is_superuser, True)
        self.assertEqual(self.second_user.is_staff, True)
        non_admin_group = PortalGroup(
            name="NonAdmins", can_admin=False)
        non_admin_group.save()
        self.second_user.portal_groups.add(non_admin_group)
        self.second_user.refresh_from_db()  # catch changes from signal handlers
        self.assertEqual(self.second_user.is_superuser, True)
        self.assertEqual(self.second_user.is_staff, True)
