"""
The custom Users model cannot be refactored into its own module:

https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#changing-to-a-custom-user-model-mid-project

Given that, it is the only model that lives on the scope here.
"""


import uuid
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.conf import settings
from multi_email_field.fields import MultiEmailField
from kubeportal.k8s import kubernetes_api

import logging

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount

logger = logging.getLogger('KubePortal')


USER_STATES = [
    ('NEW', 'not requested'),
    ('ACCESS_REQUESTED', 'requested'),
    ('ACCESS_REJECTED', 'rejected'),
    ('ACCESS_APPROVED', 'approved')
]

class User(AbstractUser):
    """
    A portal user.
    """
    NEW = 'NEW'
    ACCESS_REQUESTED = 'ACCESS_REQUESTED'
    ACCESS_REJECTED = 'ACCESS_REJECTED'
    ACCESS_APPROVED = 'ACCESS_APPROVED'

    state = models.CharField(default=NEW, 
                             verbose_name="Cluster access",
                             max_length=100,
                             help_text="The state of the cluster access approval workflow.", 
                             choices=USER_STATES)
    approval_id = models.UUIDField(
        default=uuid.uuid4, editable=False, null=True)
    answered_by = models.ForeignKey(
        'User', help_text="Which user approved the cluster access for this user.", on_delete=models.SET_NULL, null=True,
        blank=True, verbose_name="Approved by")
    comments = models.CharField(
        max_length=150, default="", null=True, blank=True)
    alt_mails = MultiEmailField(default=None, null=True, blank=True)
    portal_groups = models.ManyToManyField(
        'PortalGroup', blank=True, verbose_name='Groups', help_text="The user groups this account belongs to.",
        related_name='members')

    service_account = models.ForeignKey(
        'KubernetesServiceAccount', related_name="portal_users", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Kubernetes account", help_text="Kubernetes namespace + service account of this user.")

    def user_id(self):
        """
        Used as property by the API serializer.
        """
        return self.pk

    def all_emails(self):
        """
        Used as property by the API serializer.
        """
        return [self.email, *self.alt_mails]

    def webapps(self):
        """
        Used as property by the API serializer.
        """
        return self.web_applications(False)        


    def k8s_accounts(self):
        """
        Used as property by the API serializer.
        Prepared for future support of multiple namespaces per user.
        """
        if self.service_account:
            return KubernetesServiceAccount.objects.filter(pk = self.service_account.pk)
        else:
            return KubernetesServiceAccount.objects.none()


    def k8s_namespaces(self):
        """
        Used as property by the API serializer.
        Prepared for future support of multiple namespaces per user.
        """
        if self.service_account:
            return KubernetesNamespace.objects.filter(pk = self.service_account.namespace.pk)
        else:
            return KubernetesNamespace.objects.none()


    def has_namespace(self, namespace):
        """
        Check if this user has permissions for this Kubernetes namespace.
        This decision is based on the configuration in the portal,
        not on the RBAC situation in the cluster.
        Prepared for future support of multiple namespaces per user.
        """
        if self.service_account:
            return namespace == self.service_account.namespace.name
        else:
            return False


    def web_applications(self, include_invisible):
        """
        Returns a querset for the list of web applications allowed for this
        user.
        """
        from kubeportal.models.webapplication import WebApplication
        if include_invisible:
            return WebApplication.objects.filter(portal_groups__members__pk=self.pk).distinct()
        else:
            return WebApplication.objects.filter(portal_groups__members__pk=self.pk, link_show=True).distinct()

    def k8s_pods(self):
        """
        Returns a list of K8S pods for this user.
        """
        if self.service_account:
            return kubernetes_api.get_namespaced_pods(self.service_account.namespace.name)
        else:
            logger.error(f"Cannot determine list of pods for user {self}, since she has no service account attached.")
            return []

    def k8s_deployments(self):
        """
        Returns a list of K8 deployments for this user.
        """
        if self.service_account:
            return kubernetes_api.get_namespaced_deployments(self.service_account.namespace.name)
        else:
            logger.error(f"Cannot determine list of deployments for user {self}, since she has no service account attached.")
            return []

    def k8s_services(self):
        """
        Returns a list of K8S services for this user.
        """
        if self.service_account:
            return kubernetes_api.get_namespaced_services(self.service_account.namespace.name)
        else:
            logger.error(f"Cannot determine list of services for user {self}, since she has no service account attached.")
            return []

    def k8s_ingresses(self):
        """
        Returns a list of K8S ingresses for this user.
        """
        if self.service_account:
            return kubernetes_api.get_namespaced_ingresses(self.service_account.namespace.name)
        else:
            logger.error(f"Cannot determine list of ingresses for user {self}, since she has no service account attached.")
            return []


    def can_subauth(self, webapp):
        user_groups_with_this_app = self.portal_groups.filter(can_web_applications__in=[webapp.pk])
        allowed = user_groups_with_this_app.count() > 0
        if allowed:
            # Prevent event storm
            # logger.debug("Subauth allowed for app {} with user {} due to membership in groups".format(webapp, self))
            return True
        else:
            logger.debug(
                "Subauth not allowed for user {}, none of the user groups allows the app {}".format(self, webapp))
            return False

    def has_access_approved(self):
        result = (self.state == User.ACCESS_APPROVED and self.service_account)
        return result

    def has_access_rejected(self):
        result = (self.state == User.ACCESS_REJECTED)
        return result

    def has_access_requested(self):
        result = (self.state == User.ACCESS_REQUESTED and self.approval_id)
        return result

    @classmethod
    def inactive_users(cls):
        """
        returns a list of users that haven't logged in x months ago.
        """
        # 30 days (1 month times the amount of months we look behind)
        x_months_ago = timezone.now() - timezone.timedelta(days=30 * settings.LAST_LOGIN_MONTHS_AGO)
        result = list(cls.objects.filter(last_login__lte=x_months_ago))
        return result

    def send_access_request(self, request, administrator=None):
        """
        Requests approval for cluster access.

        Note: The parameter administrator is an optional argument which can be
              used to send an access request to a specific super user.
        """
        approve_url = request.build_absolute_uri(reverse('admin:access_approve', kwargs={'approval_id': self.approval_id}))
        reject_url  = request.build_absolute_uri(reverse('admin:access_reject',  kwargs={'approval_id': self.approval_id}))

        html_mail = render_to_string('mail_access_request.html', {'branding': settings.BRANDING,
                                                                  'user': str(self),
                                                                  'approve_url': approve_url,
                                                                  'reject_url': reject_url
                                                                  })

        text_mail = strip_tags(html_mail)
        subject = 'Request for access to "{0}"'.format(settings.BRANDING)

        cluster_admins = []

        if administrator:
            cluster_admins.append(User.objects.get(username=administrator))
            logger.info(F"Sending access request from '{self.username}' to '{administrator}'")
            logger.debug(F"Approval URL: {approve_url}")
        else:
            for admin in User.objects.filter(is_superuser=True):
                cluster_admins.append(admin)
            logger.info(F"Sending access request from '{self.username}' to all administrators")

        cluster_admin_emails = [admin.email for admin in cluster_admins]

        try:
            send_mail(subject, text_mail, settings.ADMIN_EMAIL,
                      cluster_admin_emails, html_message=html_mail, fail_silently=False)

            logger.debug(
                'Sent email to admins about access request from ' + str(self))

            self.state = self.ACCESS_REQUESTED
            self.answered_by = None
            self.save()
            return True
        except Exception:
            logger.exception(
                'Problem while sending email to admins about access request from ' + str(self))
            return False

    def reject(self, request):
        """
        Answers a approval request with "rejected".
        The state transition happens automatically, an additional information
        is send to the denied user by email.
        """
        self.service_account = None
        self.state = self.ACCESS_REJECTED
        self.answered_by = request.user
        self.save()

        messages.add_message(request, messages.INFO,
                             "Access request for '{0}' was rejected.".format(self))
        logger.info("Access for user '{0}' was rejected by user '{1}'.".format(
            self, request.user))

        html_mail = render_to_string('mail_access_rejected.html', {'branding': settings.BRANDING,
                                                                   'user': str(self),
                                                                   })

        text_mail = strip_tags(html_mail)
        subject = 'Your request for access to "{0}"'.format(settings.BRANDING)

        try:
            if self.email:
                send_mail(subject, text_mail, settings.ADMIN_EMAIL, [
                    self.email, ], html_message=html_mail, fail_silently=False)
                logger.debug(
                    "Sent email to user '{0}' about access request rejection".format(self))
        except Exception:
            logger.exception(
                "Problem while sending email to user '{0}' about access request rejection".format(self))

        return True


    def approve(self, request, new_svc):
        """
        Answers a approval request with "approved".
        """
        self.state = self.ACCESS_APPROVED
        self.service_account = new_svc
        self.answered_by = request.user
        self.save()

        messages.info(
            request,
            "User '{0}' is now assigned to existing Kubernetes namespace '{1}'.".format(self, new_svc.namespace))
        logger.info(
            "User '{0}' was assigned to existing Kubernetes namespace {1} by {2}.".format(self, new_svc.namespace,
                                                                                          request.user))

        html_mail = render_to_string('mail_access_approved.html', {'branding': settings.BRANDING,
                                                                   'user': str(self),
                                                                   })

        text_mail = strip_tags(html_mail)
        subject = 'Your request for access to the {0} Kubernetes Cluster'.format(
            settings.BRANDING)

        try:
            if self.email:
                send_mail(subject, text_mail, settings.ADMIN_EMAIL, [
                    self.email, ], html_message=html_mail, fail_silently=False)
                logger.debug(
                    "Sent email to user '{0}' about access request approval".format(self))
                messages.info(
                    request, "User '{0}' informed by eMail.".format(self))
        except Exception:
            logger.exception(
                "Problem while sending email to user '{0}' about access request approval".format(self))
            messages.error(
                request, "Problem while sending information to user '{0}' by eMail.".format(self))

        return True

    def approve_link(self):
        if self.has_access_requested():
            uri = reverse('admin:access_approve', kwargs={
                'approval_id': self.approval_id})
            return mark_safe('<a class="grp-button" href="{0}" target="blank">Approve request</a>'.format(uri))
        else:
            return None

    approve_link.short_description = 'Action'

    @property
    def token(self):
        from kubeportal.k8s.kubernetes_api import get_token
        try:
            return get_token(self.service_account)
        except Exception:
            return None
