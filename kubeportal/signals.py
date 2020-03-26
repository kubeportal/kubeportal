from django.db.models.signals import post_save
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import Group as PortalGroup

from django.contrib.auth.models import Group, Permission
import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def auto_add_portal_groups(sender, instance, **kwargs):
    for group in PortalGroup.objects.all():
        if group.auto_add:
            logger.debug("Automatically adding user {0} to group {1}".format(instance, group))
            group.members.add(instance)
            group.save()


@receiver(post_save, sender=User)
def create_permission_groups(sender, instance, **kwargs):
    '''
    Django permissions are created long after the inital
    migration and the createsuperuser run. These reasons
    for that are kind of fuzzy, but this leads to the fact
    that this signal handler silently fails when createsuperuser
    is used directly after the installion, due to missing permission
    objects.

    It does not fail, however, later when the first real user
    is created, either through Python Social or an admin
    activity in the backend. And this is good enough, the superuser
    does not need permissions anyway.
    '''
    # Make sure the default permission group exists
    admin_group, created = Group.objects.get_or_create(
        name='Account Administrators')

    # Reflect staff status in permission group membership, so that group
    # permissions regulate the backend access details
    if instance.is_staff:
        logger.debug("Automatically adding backend permissions for user {0}".format(instance))
        instance.groups.add(admin_group)
    else:
        logger.debug("Automatically removing backend permissions for user {0}".format(instance))
        instance.groups.remove(admin_group)

    # Set all permissions for the default permission group
    try:
        for perm_name in ['Can add user',
                          'Can change user',
                          'Can delete user',
                          'Can add OAuth2 Application',
                          'Can change OAuth2 Application',
                          'Can view OAuth2 Application',
                          'Can delete OAuth2 Application',
                          'Can add kubernetes namespace',
                          'Can change kubernetes namespace',
                          'Can view kubernetes namespace',
                          'Can add kubernetes service account',
                          'Can change kubernetes service account',
                          'Can view kubernetes service account',
                          'Can add link',
                          'Can change link',
                          'Can delete link',
                          'Can add Client',
                          'Can change Client',
                          'Can delete Client',
                          'Can view Client']:
            perm = Permission.objects.get(name=perm_name)
            admin_group.permissions.add(perm)
        admin_group.save()
    except Exception:
        pass
