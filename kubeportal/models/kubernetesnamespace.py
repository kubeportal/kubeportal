from django.db import models
from django.db.models import Count
from ..k8s import kubernetes_api as api

class KubernetesNamespace(models.Model):
    """
    A replication of namespaces known to the API server.
    """
    name = models.CharField(
        max_length=100,
        help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    visible = models.BooleanField(
        default=True, help_text='Visibility in admin interface. Can only be configured by a superuser.')

    def __str__(self):
        return self.name

    def is_synced(self):
        return self.uid is not None

    @classmethod
    def without_service_accounts(cls):
        """
        returns a list of namespaces without a service account
        """
        visible_namespaces = cls.objects.filter(visible=True)
        counted_service_accounts = visible_namespaces.annotate(Count('service_accounts'))
        return [ns for ns in counted_service_accounts if ns.service_accounts__count == 0]

    @classmethod
    def without_pods(cls):
        """
        returns a list of namespaces without pods
        """
        visible_namespaces = cls.objects.filter(visible=True)
        namespaces_without_pods = []
        pod_list = api.get_pods()
        for ns in visible_namespaces:
            ns_has_pods = False
            for pod in pod_list:
                if pod.metadata.namespace == ns.name:
                    ns_has_pods = True
                    break
            if not ns_has_pods:
                namespaces_without_pods.append(ns)
        return namespaces_without_pods
