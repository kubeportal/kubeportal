from django.contrib.auth.models import AbstractUser
from django.contrib import messages
from django.db import models
from django_fsm import FSMField, transition
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags, mark_safe
from oidc_provider.models import Client
import uuid
import logging
import oidc_provider

logger = logging.getLogger('KubePortal')


class KubernetesNamespace(models.Model):
    '''
    A replication of namespaces known to the API server.
    '''
    name = models.CharField(
        max_length=100, help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    visible = models.BooleanField(
        default=True, help_text='Visibility in admin interface. Can only be configured by a superuser.')

    def __str__(self):
        return self.name

    def is_synced(self):
        return self.uid is not None


class KubernetesServiceAccount(models.Model):
    '''
    A replication of service accounts known to the API server.
    '''
    name = models.CharField(
        max_length=100, help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    namespace = models.ForeignKey(
        KubernetesNamespace, related_name="service_accounts", on_delete=models.CASCADE)

    def __str__(self):
        return "{1}:{0}".format(self.name, self.namespace)

    def is_synced(self):
        return self.uid is not None


class UserState():
    NEW = 'not requested'
    ACCESS_REQUESTED = 'requested'
    ACCESS_REJECTED = 'rejected'
    ACCESS_APPROVED = 'approved'


user_state_list = ((UserState.NEW, UserState.NEW),
                   (UserState.ACCESS_REQUESTED, UserState.ACCESS_REQUESTED),
                   (UserState.ACCESS_REJECTED, UserState.ACCESS_REJECTED),
                   (UserState.ACCESS_APPROVED, UserState.ACCESS_APPROVED)
                   )


class User(AbstractUser):
    '''
    A portal user.
    '''
    state = FSMField(default=UserState.NEW, verbose_name="Cluster access",
                     help_text="The state of the cluster access approval workflow.", choices=user_state_list)
    approval_id = models.UUIDField(
        default=uuid.uuid4, editable=False, null=True)
    answered_by = models.ForeignKey(
        'User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Approved by")
    comments = models.CharField(
        max_length=150, help_text="Description on why this user needs cluster access. (150 characters)", default="", null=True, blank=True)

    service_account = models.ForeignKey(
        KubernetesServiceAccount, related_name="portal_users", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kubernetes account", help_text="Kubernetes namespace + service account of this user.")

    def has_access_approved(self):
        return self.state == UserState.ACCESS_APPROVED and self.service_account

    def has_access_rejected(self):
        return self.state == UserState.ACCESS_REJECTED

    def has_access_requested(self):
        return self.state == UserState.ACCESS_REQUESTED and self.approval_id

    @transition(field=state, source=[UserState.NEW, UserState.ACCESS_REQUESTED, UserState.ACCESS_APPROVED, UserState.ACCESS_REJECTED], target=UserState.ACCESS_REQUESTED)
    def send_access_request(self, request):
        '''
        Requests approval for cluster access.

        Note: The user object must be saved by the caller, to reflect the state change,
              when this method returns "True".
        '''
        self.approval_id = uuid.uuid4()

        html_mail = render_to_string('mail_access_request.html', {'branding': settings.BRANDING,
                                                                  'user': str(self),
                                                                  'approve_url': request.build_absolute_uri(reverse('admin:access_approve', kwargs={'approval_id': self.approval_id})),
                                                                  'reject_url': request.build_absolute_uri(reverse('admin:access_reject', kwargs={'approval_id': self.approval_id}))
                                                                  })

        text_mail = strip_tags(html_mail)
        subject = 'Request for access to "{0}"'.format(settings.BRANDING)

        cluster_admins = User.objects.filter(
            is_staff=True).values_list('email', flat=True)

        try:
            send_mail(subject, text_mail, settings.ADMIN_EMAIL,
                      cluster_admins, html_message=html_mail, fail_silently=False)
            logger.debug(
                'Sent email to admins about access request from ' + str(self))
            return True
        except Exception:
            logger.exception(
                'Problem while sending email to admins about access request from ' + str(self))
            return False

    @transition(field=state, source='*', target=UserState.ACCESS_REJECTED)
    def reject(self, request):
        '''
        Answers a approval request with "rejected".
        The state transition happens automatically, an additional information
        is send to the denied user by email.

        Note: The user object must be saved by the caller, to reflect the state change,
              when this method returns "True".
        '''
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

        # overwrite old approval, if URL is used again by the admins
        self.service_account = None
        self.answered_by = request.user
        return True

    @transition(field=state, source='*', target=UserState.ACCESS_APPROVED)
    def approve(self, request, new_svc):
        '''
        Answers a approval request with "approved".
        The state transition happens automatically.

        Note: The user object must be saved by the caller, to reflect the state change,
              when this method returns "True".
        '''
        self.service_account = new_svc
        self.answered_by = request.user
        messages.info(
            request, "User '{0}' is now assigned to existing Kubernetes namespace '{1}'.".format(self, new_svc.namespace))
        logger.info(
            "User '{0}' was assigned to existing Kubernetes namespace {1} by {2}.".format(self, new_svc.namespace, request.user))

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
    approve_link.short_description = ('Action')

    @property
    def token(self):
        from kubeportal.kubernetes import get_token
        try:
            return get_token(self.service_account)
        except Exception:
            return None


class WebApplication(models.Model):
    '''
    A web application protected and / or linked by KubePortal.
    '''
    name = models.CharField(max_length=100)
    link_show = models.BooleanField(
        verbose_name="Show link on welcome page", default=False)
    link_name = models.CharField(
        null=True, blank=True,
        verbose_name="Link title",
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the title.", max_length=100)
    link_url = models.URLField(
        null=True, blank=True,
        verbose_name="Link URL",
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the URL.")
    oidc_client = models.OneToOneField(Client, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Client settings")
    class Meta:
        verbose_name = 'web application'

    def __str__(self):
        return self.name


class Group(models.Model):
    '''
    A group of portal users.
    '''
    name = models.CharField(
        max_length=100, verbose_name='Name for the user group')
    members = models.ManyToManyField(
        User, blank=True, verbose_name='Members of the user group', related_name='portal_groups')
    web_applications = models.ManyToManyField(
        WebApplication, blank=True, verbose_name='Web applications enabled for this user group', related_name='portal_groups')

    def __str__(self):
        return self.name
