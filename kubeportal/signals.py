from django.db.models.signals import post_save
from django.dispatch import receiver

from kubeportal.models import User
from kubeportal.models import PortalGroup

from django.contrib.auth.models import Group, Permission
import logging

logger = logging.getLogger('KubePortal')


@receiver(post_save, sender=User)
def handle_user_change(sender, instance, **kwargs):
    member_of_auto_admin_group = False
    for group in PortalGroup.objects.all():
        if group.auto_add:
            logger.debug("Making sure that user {0} is in auto-add group {1}".format(instance, group))
            group.members.add(instance)
            group.save()
        if group.auto_admin and group.has_member(instance) and not instance.is_staff:
            logger.debug("Enabling admin rights for user {0} due to group membership in {1}".format(instance, group))
            instance.is_staff = True
            instance.save()
            member_of_auto_admin_group = True
    if not member_of_auto_admin_group and instance.is_staff:
        logger.debug("Disabling admin rights for user {0}, not in any auto-admin group".format(instance))
        instance.is_staff = False
        instance.save()

@receiver(post_save, sender=PortalGroup)
def handle_group_change(sender, instance, **kwargs):
    for member in instance.members.all():
        if instance.auto_admin and not member.is_staff:
            logger.debug("Enabling admin rights for user {0} due to group membership in {1}".format(instance, group))
            instance.is_staff = True
            instance.save()
        if not instance.auto_admin and member.is_staff:
            found_another_auto_admin_group = False
            for group in PortalGroup.objects.all():
                if group.auto_admin and group.pk != instance.pk:
                    found_another_auto_admin_group = True
            if not found_another_auto_admin_group:
                logger.debug("Disabling admin rights for user {0}, no longer in any auto-admin group".format(instance))
                instance.is_staff = False
                instance.save()

