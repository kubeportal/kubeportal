from django.db.models.signals import post_save
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

from django.contrib.auth.models import Group, Permission
import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, **kwargs):
    user_in_auto_admin_group = False
    for group in PortalGroup.objects.all():
        if group.auto_add:
            logger.debug("Making sure that user {0} is in auto-add group {1}".format(instance, group))
            group.members.add(instance)
            group.save()
        if group.auto_admin and not instance.is_staff:
            logger.info("Enabling missing admin rights for user {0} due to user change, based on membership in auto-admin group {1}".format(instance, group))
            instance.is_staff = True
            instance.save()
            user_in_auto_admin_group = True
    if not user_in_auto_admin_group and instance.is_staff:
        logger.info("Removing admin rights for user {0}, no membership in auto-admin group found.".format(instance))
        instance.is_staff = False
        instance.save()

@receiver(post_save, sender=PortalGroup)
def handle_group_change(sender, instance, **kwargs):
    for user in User.objects.all():
        if instance.auto_admin:
            if instance.has_member(user) and not user.is_staff:
                logger.info("Enabling missing admin rights for user {0} due to group change, based on membership in auto-admin group {1}".format(user, instance))
        else:
            # check if users exist that have no auto-admin group anymore, remove flag from them

