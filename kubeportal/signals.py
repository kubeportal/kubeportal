from django.db.models.signals import post_save
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

from django.contrib.auth.models import Group, Permission
import logging

logger = logging.getLogger('KubePortal')

@receiver(post_save, sender=User)
def auto_add_portal_groups(sender, instance, **kwargs):
    '''
    Portal groups have a flag for new users being added automatically.
    One use case is a "all users" group.
    This signal handlers manages the addition of new users to this group.
    This works regardless of any other permissions. It also runs on every login,
    since the last login date is updated.
    '''
    for group in PortalGroup.objects.all():
        if group.auto_add:
            logger.debug("Automatically adding user {0} to group {1}".format(instance, group))
            group.members.add(instance)
            group.save()



