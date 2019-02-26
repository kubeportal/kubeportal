from django.contrib.auth.models import AbstractUser
from django.db import models
from oauth2_provider.models import AbstractApplication


class OAuth2Application(AbstractApplication):
    '''
    A tailored version of the OAuth2 application config.
    '''
    skip_authorization = models.BooleanField(
        default=True,
        help_text='Skip separate authorization page after successful login?')
    authorization_grant_type = models.CharField(
        max_length=32,
        choices=AbstractApplication.GRANT_TYPES,
        default=AbstractApplication.GRANT_AUTHORIZATION_CODE)
    client_type = models.CharField(
        max_length=32,
        choices=AbstractApplication.CLIENT_TYPES,
        default=AbstractApplication.CLIENT_CONFIDENTIAL)


class KubernetesNamespace(models.Model):
    '''
    A replication of namespaces known to the API server.
    '''
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=50, null=True, editable=False)

    def __str__(self):
        return self.name


class KubernetesServiceAccount(models.Model):
    '''
    A replication of service accounts known to the API server.
    '''
    name = models.CharField(max_length=100)
    uid = models.CharField(max_length=50, null=True, editable=False)
    namespace = models.ForeignKey(
        KubernetesNamespace, on_delete=models.CASCADE)

    def __str__(self):
        return "{1}:{0}".format(self.name, self.namespace)


class User(AbstractUser):
    '''
    A Django user, extended by some fields.
    '''
    service_account = models.ForeignKey(
        KubernetesServiceAccount, on_delete=models.SET_NULL, null=True, blank=True)

    def token(self):
        from kubeportal.kubernetes import get_token
        return get_token(self.service_account)


class ClusterApplication(models.Model):
    '''
    Cluster applications to be shown in the frontend.
    '''
    name = models.CharField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the title.", max_length=100)
    url = models.URLField(
        help_text="You can use the placeholders '{{namespace}}' and '{{serviceaccount}}' in the URL.")

    def __str__(self):
        return self.name
