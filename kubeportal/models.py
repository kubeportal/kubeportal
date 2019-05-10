from django.contrib.auth.models import AbstractUser
from django.db import models


class KubernetesNamespace(models.Model):
    '''
    A replication of namespaces known to the API server.
    '''
    name = models.CharField(max_length=100, help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    visible = models.BooleanField(default=True, help_text='Visibility in admin interface. Can only be configured by a superuser.')

    def __str__(self):
        return self.name

    def is_synced(self):
        return self.uid is not None


class KubernetesServiceAccount(models.Model):
    '''
    A replication of service accounts known to the API server.
    '''
    name = models.CharField(max_length=100, help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    namespace = models.ForeignKey(
        KubernetesNamespace, on_delete=models.CASCADE)

    def __str__(self):
        return "{1}:{0}".format(self.name, self.namespace)

    def is_synced(self):
        return self.uid is not None


class User(AbstractUser):
    '''
    A Django user, extended by some fields.
    '''
    service_account = models.ForeignKey(
        KubernetesServiceAccount, on_delete=models.SET_NULL, null=True, blank=True, help_text="The security token of this service account is provided for the user.")

    @property
    def token(self):
        from kubeportal.kubernetes import get_token
        return get_token(self.service_account)


class Link(models.Model):
    '''
    Links to be shown in the frontend.
    '''
    name = models.CharField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the title.", max_length=100)
    url = models.URLField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the URL.")

    def __str__(self):
        return self.name

