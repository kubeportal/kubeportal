from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, created, **kwargs):
    '''
    Handle changes of user attributes.
    Group membership are handled separately.
    '''
    if created:
        logger.debug("Creation of user {0} detected.".format(instance))
        for group in PortalGroup.objects.all():
            if group.auto_add_new:
                logger.debug("Making sure that new user {0} is in auto-add-new group {1}".format(instance, group))
                group.members.add(instance)
                group.save()
    else:
        logger.debug("Change of user {0} detected.".format(instance))
        if instance.has_access_approved():
            for group in PortalGroup.objects.all():
                if group.auto_add_approved:
                    logger.debug("Making sure that user {0} is in auto-add-approved group {1}".format(instance, group))
                    group.members.add(instance)


def _set_staff_status(user):
    '''
    Check if the user should have staff status, and set it accordingly.
    '''
    if user.is_superuser:      # Do not touch the is_staff attribute of superusers
        return

    in_can_admin_group = user.portal_groups.filter(can_admin=True).exists()
    if not in_can_admin_group and user.is_staff:
        logger.info("Disabling existing admin rights for user {0}.".format(user))
        user.is_staff = False
        user.save()
    if in_can_admin_group and not user.is_staff:
        logger.info("Enabling missing admin rights for user {0}.".format(user))
        user.is_staff = True
        user.save()


@receiver(m2m_changed, sender=User.portal_groups.through)
def handle_group_members_change(instance, action, pk_set, reverse, **kwargs):
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


@receiver(post_save, sender=PortalGroup)
def handle_group_change(sender, instance, created, **kwargs):
    '''
    Handle changes of portal group attributes.
    Group membership are handled separately.
    '''
    if created:
        logger.debug("Creation of portal group {0} detected.".format(instance))
    else:
        logger.debug("Change of portal group {0} detected.".format(instance))
        for user in instance.members.all():
            _set_staff_status(user)

