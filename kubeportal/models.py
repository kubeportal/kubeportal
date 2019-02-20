from django.contrib.auth.models import User
from django.db import models


class KubernetesNamespace(models.Model):
    '''
    A replication of namespaces known to the API server.
    '''
    name = models.CharField(max_length=100)


class KubernetesServiceAccount(models.Model):
    '''
    A replication of service accounts known to the API server.
    '''
    name = models.CharField(max_length=100)
    namespace = models.ForeignKey(KubernetesNamespace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class ClusterApplication(models.Model):
    '''
    Cluster applications to be shown in the frontend.
    '''
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.name