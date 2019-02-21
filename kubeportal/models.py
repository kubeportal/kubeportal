from django.contrib.auth.models import AbstractUser
from django.db import models


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
    namespace = models.ForeignKey(KubernetesNamespace, on_delete=models.CASCADE)

    def __str__(self):
        return "{0} ({1})".format(self.name, self.namespace)


class User(AbstractUser):
    svcaccount = models.ForeignKey(KubernetesServiceAccount, on_delete=models.SET_NULL, null=True)


class ClusterApplication(models.Model):
    '''
    Cluster applications to be shown in the frontend.
    '''
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.name
