from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, created, **kwargs):
    # Avoid recursion of post_save handler when changing the instance
    if hasattr(instance, '_dirty'):
        return

    # Do not touch superusers
    if instance.is_superuser:
        return

    logger.debug("Change of user detected.")

    member_of_can_admin_group = False
    for group in PortalGroup.objects.all():
        if group.auto_add_new and created:
            logger.debug("Making sure that new user {0} is in auto-add-new group {1}".format(instance, group))
            group.members.add(instance)
            group.save()
        if group.can_admin and group.has_member(instance):
            # Remember that we found the user in one of the admin groups.
            # Fix staff flag, if needed.
            member_of_can_admin_group = True
            logger.debug("User {0} is in can_admin group {1}".format(instance, group))
            if not instance.is_staff:
                logger.debug("Enabling missing admin rights for user {0} due to group membership in {1}".format(instance, group))
                instance.is_staff = True
                try:
                    instance._dirty = True
                    instance.save()
                finally:
                    del instance._dirty

    if not member_of_can_admin_group and instance.is_staff:
        logger.debug("Disabling admin rights for user {0}, not in any can_admin group".format(instance))
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
    # Do not touch superusers
    if user.is_superuser:
        return

    in_can_admin_group = user.portal_groups.filter(can_admin=True).exists()
    logger.debug("User {0} in auto_admin group: {1}".format(user, in_can_admin_group))
    if not in_can_admin_group and user.is_staff:
        logger.info("Disabling existing admin rights for user {0} due to group membership change.".format(user))
        user.is_staff = False
        user.save()
    if in_can_admin_group and not user.is_staff:
        logger.info("Enabling missing admin rights for user {0} due to group membership change.".format(user))
        user.is_staff = True
        user.save()


@receiver(m2m_changed, sender=User.portal_groups.through)
def handle_group_change(instance, action, pk_set, reverse, **kwargs):
    '''
    Only members of an auto-admin group should have staff permissions.

    Note: We could implement a large logic here, based on the knowledge of the M2M action (add/remove/...).
    This could save us from looping over all affected users in reverse=True cases, but becomes kind of complex.
    We skip that, and favour code simplicity over performance here.
    '''
    # Skip the "pre_" events
    if action not in ["post_add", "post_remove"]:
        return

    if reverse:
        group = instance
        logger.debug("Members of group {0} were changed.".format(group))
        for user_pk in pk_set:
            user = User.objects.get(pk=user_pk)
            _set_staff_status(user)
    else:
        user = instance
        logger.debug("Groups of user {0} were changed.".format(user))
        _set_staff_status(user)

