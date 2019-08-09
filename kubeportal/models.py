from django.contrib.auth.models import AbstractUser
from django.db import models
from django_fsm import FSMField, transition
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import uuid
import logging


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
        KubernetesNamespace, on_delete=models.CASCADE)

    def __str__(self):
        return "{1}:{0}".format(self.name, self.namespace)

    def is_synced(self):
        return self.uid is not None


class UserState():
    NEW = 'new'
    ACCESS_REQUESTED = 'requested'
    ACCESS_REJECTED = 'rejected'
    ACCESS_APPROVED = 'approved'


class User(AbstractUser):
    '''
    A Django user, extended by some fields.
    '''

    state = FSMField(default=UserState.NEW)
    approval_id = models.UUIDField(default=uuid.uuid4, editable=False)

    service_account = models.ForeignKey(
        KubernetesServiceAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="The security token of this service account is provided for the user.")

    def has_access_approved(self):
        return self.state == UserState.ACCESS_APPROVED and self.service_account

    def has_access_requested(self):
        return self.state == UserState.ACCESS_REQUESTED

    @transition(field=state, source=[UserState.NEW, UserState.ACCESS_REQUESTED, UserState.ACCESS_REJECTED], target=UserState.ACCESS_REQUESTED)
    def send_access_request(self, request):
        '''
        Sends mail about approval request to all backend admins.
        '''
        self.approval_id = uuid.uuid4()
        self.save()

        html_mail = render_to_string('mail_access_request.html', {'branding': settings.BRANDING,
                                                                  'user': str(self),
                                                                  'approve_url': request.build_absolute_uri(reverse('access_approve', kwargs={'approval_id': self.approval_id})),
                                                                  'deny_url': request.build_absolute_uri(reverse('access_deny', kwargs={'approval_id': self.approval_id}))
                                                                  })

        text_mail = strip_tags(html_mail)
        subject = 'Request for access to {0} Kubernetes Cluster'.format(settings.BRANDING)

        cluster_admins = User.objects.filter(
            is_staff=True).values_list('email', flat=True)

        try:
            send_mail(subject, text_mail, settings.ADMIN_EMAIL, cluster_admins, html_message=html_mail, fail_silently=False)
            logger.debug(
                'Sent email to admins about access request from ' + str(self))
            return True
        except Exception:
            logger.exception(
                'Problem while sending email to admins about access request from ' + str(self))
            return False

    @transition(field=state, source='*', target=UserState.ACCESS_REJECTED)
    def deny(self):
        pass

    @transition(field=state, source='*', target=UserState.ACCESS_APPROVED)
    def allow(self):
        pass

    @property
    def token(self):
        from kubeportal.kubernetes import get_token
        return get_token(self.service_account)


class Link(models.Model):
    '''
    Links to be shown in the frontend.
    '''
    name=models.CharField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the title.", max_length=100)
    url=models.URLField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the URL.")

    def __str__(self):
        return self.name
