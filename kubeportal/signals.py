from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Permission

import logging

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models import User

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, created, **kwargs):
    '''
    Handle changes of user attributes:
    - New user comes to the system, must be member of "all" special group.
    - User gets approval state change, must be reflected in "k8s" special group.
    '''
    logger.debug("Change of user {0} detected.".format(instance))

    # The index is just a safeguard for broken databases
    # There should be only one of them per type
    all_group = PortalGroup.objects.filter(special_all_accounts=True)[0]
    k8s_group = PortalGroup.objects.filter(special_k8s_accounts=True)[0]

    if not instance.portal_groups.filter(pk=all_group.pk).exists():
        logger.info("Putting user {0} into special group for all users".format(instance))
        all_group.members.add(instance)

    if instance.has_access_approved() and not instance.portal_groups.filter(pk=k8s_group.pk).exists():
        logger.info("Putting user {0} into special group for Kubernetes users".format(instance))
        k8s_group.members.add(instance)

    if not instance.has_access_approved() and instance.portal_groups.filter(pk=k8s_group.pk).exists():
        logger.info("Removing user {0} from special group for Kubernetes users".format(instance))
        k8s_group.members.remove(instance)


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
        # This is a safe guard for cases where new backend models came after
        # the user was created. Otherwise, the backend user still would not have
        # the model permissions for seing the admin pages accordingly.
        all_perms = Permission.objects.all()
        user.user_permissions.add(*all_perms)

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

