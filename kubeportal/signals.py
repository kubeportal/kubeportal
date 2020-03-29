from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

from django.contrib.auth.models import Group, Permission
import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, **kwargs):
    # Avoid recursion of post_save handler when changing the instance
    if hasattr(instance, '_dirty'):
        return

    member_of_auto_admin_group = False
    for group in PortalGroup.objects.all():
        if group.auto_add:
            logger.debug("Making sure that user {0} is in auto-add group {1}".format(instance, group))
            group.members.add(instance)
            group.save()
        if group.auto_admin and group.has_member(instance) and not instance.is_staff:
            logger.debug("Enabling admin rights for user {0} due to group membership in {1}".format(instance, group))
            instance.is_staff = True
            try:
                instance._dirty = True
                instance.save()
            finally:
                del instance._dirty
                member_of_auto_admin_group = True
    if not member_of_auto_admin_group and instance.is_staff:
        logger.debug("Disabling admin rights for user {0}, not in any auto-admin group".format(instance))
        instance.is_staff = False
        try:
            instance._dirty = True
            instance.save()
        finally:
            del instance._dirty

def _set_staff_status(user):
    '''
    Check if the user should have staff status, and set it accordingly.
    '''
    in_auto_admin_group = user.portal_groups.filter(auto_admin=True).exists()
    if not in_auto_admin_group and user.is_staff:
        logger.info("Disabling existing admin rights for user {0} due to group membership change.".format(user))
        user.is_staff = False
        user.save()
    if in_auto_admin_group and not user.is_staff:
        logger.info("Enabling missing admin rights for user {0} due to group membership change.".format(user))
        user.is_staff = True
        user.save()


@receiver(m2m_changed, sender=User.portal_groups.through)
def handle_group_change(instance, action, pk_set, reverse, **kwargs):
    '''
    Only users being members in an auto-admin group should have staff permissions.

    Note: We could implement a large logic here, based on the knowledge of post_add and post_remove being triggered.
    This could save some time for checking all user groups for every user being touched by this signal.
    We skip that and favour code simplicity over performance here.
    '''
    if action not in ["post_add", "post_remove"]:
        return

    if reverse:
        group = instance
        for user_pk in pk_set:
            user = User.objects.get(pk=user_pk)
            _set_staff_status(user)
    else:
        user = instance
        _set_staff_status(user)

