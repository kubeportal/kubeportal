from django.db import models

from kubeportal.models.webapplication import WebApplication


class PortalGroup(models.Model):
    """
    A group of portal users.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Name')
    special_k8s_accounts = models.BooleanField(
        default=False)  # special group, automatically contains all k8s account holders
    special_all_accounts = models.BooleanField(
        default=False)  # special group, automatically contains all accounts
    can_admin = models.BooleanField(
        verbose_name="Backend access",
        help_text="Enabling this allows members of this group to access the administrative backend.",
        default=False)
    can_web_applications = models.ManyToManyField(
        WebApplication,
        blank=True,
        verbose_name='Web applications',
        help_text="Web applications that are accessible for members of this group.",
        related_name='portal_groups')

    def __str__(self):
        return self.name

    def is_special_group(self):
        """ Returns if this is a special group with automatic member management."""
        return self.special_k8s_accounts or self.special_all_accounts

    def has_member(self, user):
        return self.members.filter(pk=user.pk).exists()

    class Meta:
        verbose_name = "User Group"
