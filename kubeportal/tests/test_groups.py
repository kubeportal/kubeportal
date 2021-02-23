"""
Tests for the user group functionality in the portal.
"""

import pytest
from django.contrib.auth.models import Permission

from kubeportal.models.portalgroup import PortalGroup


def test_model_methods(second_user):
    admin_group = PortalGroup(name="Admins", can_admin=True)
    admin_group.save()
    admin_group.members.add(second_user)
    assert admin_group.has_member(second_user) is True


def test_admin_attrib_modification_with_members(second_user):
    future_admin_group = PortalGroup(name="Admins", can_admin=False)
    future_admin_group.save()
    future_admin_group.members.add(second_user)
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is False
    future_admin_group.can_admin = True
    future_admin_group.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is True
    future_admin_group.can_admin = False
    future_admin_group.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is False


def test_admin_attrib_add_remove_user(second_user):
    # Create admin group
    admin_group = PortalGroup(name="Admins", can_admin=True)
    admin_group.save()
    # Non-member should not become admin
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is False
    # make member, should become admin
    admin_group.members.add(second_user)
    admin_group.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is True
    # remove again from group, shopuld lose admin status
    admin_group.members.remove(second_user)
    admin_group.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is False


def test_admin_attrib_multiple(second_user):
    # create two admin groups
    admin_group1 = PortalGroup(name="Admins1", can_admin=True)
    admin_group1.save()
    admin_group2 = PortalGroup(name="Admins2", can_admin=True)
    admin_group2.save()
    # add same person to both groups
    admin_group1.members.add(second_user)
    admin_group2.members.add(second_user)
    admin_group1.save()
    admin_group2.save()
    # person should be admin now
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is True
    # remove from first group, should still be admin
    admin_group1.members.remove(second_user)
    admin_group1.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is True
    # remove from second group, should lose admin status
    admin_group2.members.remove(second_user)
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_staff is False


def test_permission_adjustment(second_user):
    assert second_user.user_permissions.all().count() == 0
    # Create admin group
    admin_group = PortalGroup(name="Admins", can_admin=True)
    admin_group.save()
    # make member, should get all model permissions
    admin_group.members.add(second_user)
    admin_group.save()
    second_user.refresh_from_db()  # catch changes from signal handlers
    perm_count = Permission.objects.count()
    assert second_user.user_permissions.all().count() == perm_count


def test_forward_relation_change(second_user):
    """
    Test the case that a user get her groups changed, not the other way around.
    """
    admin_group = PortalGroup(name="Admins", can_admin=True)
    admin_group.save()
    assert admin_group.members.count() == 0
    assert second_user.is_staff is False
    second_user.portal_groups.add(admin_group)
    second_user.save()
    assert admin_group.members.count() == 1
    assert second_user.is_staff is True


def test_dont_touch_superuser(second_user):
    """
    The can_admin signal handler magic should not be applied to superusers,
    otherwise they may loose the backend access when not
    be a member of an admin group.
    """
    second_user.is_superuser = True
    second_user.is_staff = True
    second_user.username = "NewNameToTriggerSignalHandler"
    second_user.save()
    assert second_user.is_superuser is True
    assert second_user.is_staff is True
    non_admin_group = PortalGroup(
        name="NonAdmins", can_admin=False)
    non_admin_group.save()
    second_user.portal_groups.add(non_admin_group)
    second_user.refresh_from_db()  # catch changes from signal handlers
    assert second_user.is_superuser is True
    assert second_user.is_staff is True

@pytest.mark.django_db
def test_special_groups():
    """
    With a fresh database, only the three special groups created by migrations exist.
    """
    for group in PortalGroup.objects.all():
        assert group.special_k8s_accounts or group.special_all_accounts or group.name == "Admin users"


