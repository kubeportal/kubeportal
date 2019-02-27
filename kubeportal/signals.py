from django.db.models.signals import post_save
from django.dispatch import receiver

from kubeportal.models import User
from django.contrib.auth.models import Group, Permission


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
    # Make sure the default group exists
    admin_group, created = Group.objects.get_or_create(
        name='Account Administrators')

    # Reflect staff status in group membership, so that group
    # permissions regulate the backend access details
    if instance.is_staff:
        instance.groups.add(admin_group)
    else:
        instance.groups.remove(admin_group)

    # Set all permissions for the default group
    try:
        for perm_name in ['Can add user',
                          'Can change user',
                          'Can delete user',
                          'Can add kubernetes namespace',
                          'Can view kubernetes namespace',
                          'Can add kubernetes service account',
                          'Can view kubernetes service account',
                          'Can add link',
                          'Can change link',
                          'Can delete link',
                          'Can view link']:
            perm = Permission.objects.get(name=perm_name)
            admin_group.permissions.add(perm)
        admin_group.save()
    except Exception:
        pass
