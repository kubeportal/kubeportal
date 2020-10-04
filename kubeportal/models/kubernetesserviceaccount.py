from django.db import models

from kubeportal.models.kubernetesnamespace import KubernetesNamespace


class KubernetesServiceAccount(models.Model):
    """
    A replication of service accounts known to the API server.
    """
    name = models.CharField(
        max_length=100, help_text="Lower case alphanumeric characters or '-', and must start and end with an alphanumeric character (e.g. 'my-name', or '123-abc').")
    uid = models.CharField(max_length=50, null=True, editable=False)
    namespace = models.ForeignKey(
        KubernetesNamespace, related_name="service_accounts", on_delete=models.CASCADE)

    def is_synced(self):
        return self.uid is not None

    def __str__(self):
        """
        Used on welcome page for showing the users Kubernetes account.
        """
        return "{1}:{0}".format(self.name, self.namespace)
