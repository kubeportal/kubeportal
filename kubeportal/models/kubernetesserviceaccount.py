from django.db import models

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.k8s import kubernetes_api as api

import logging

logger = logging.getLogger('KubePortal')


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

    @classmethod
    def create_missing_in_portal(cls):
        """
        Scans the Kubernetes cluster for service accounts that have no representation
        as KubernetesServiceAccount object, and creates the latter accordingly.
        """
        try:
            k8s_svca_list = api.get_service_accounts()
            if k8s_svca_list:
                for k8s_svca in k8s_svca_list:
                    # First calling exists(), and creating it in case, is faster than get_or_create() 
                    # but may impose an extremely small danger of race conditions.
                    # We trade performance for reliability here. 
                    if not cls.objects.filter(name=k8s_svca.metadata.name, uid=k8s_svca.metadata.uid).exists():
                        logger.info(f"Found new Kubernetes service account {k8s_svca.metadata.name}, creating record.")
                        ns = KubernetesNamespace.get_or_sync(k8s_svca.metadata.namespace)
                        new_obj = cls(name=k8s_svca.metadata.name, uid=k8s_svca.metadata.uid, namespace=ns)
                        new_obj.save()
            return  True
        except Exception as e:
            logger.exception(f"Syncing new cluster service accounts into the portal failed.")
            return False


    @classmethod
    def create_missing_in_cluster(cls):
        """
        Scans the portal database for service accounts that have no representation
        in the Kubernetes cluster, and creates the latter accordingly.
        """
        try:
            # Create a list of cluster service account UIDs that already exist
            k8s_svca_uid_list = [k8s_svca.metadata.uid for k8s_svca in api.get_service_accounts()]

            # Scan portal service account entries
            for portal_svca in cls.objects.all():
                if portal_svca.uid:
                    # Portal records with UID must be given in K8S, or they are stale und should be deleted
                    if portal_svca.uid not in k8s_svca_uid_list:
                        logger.warning(f"Removing stale service account record '{portal_svca.namespace.name}:{portal_svca.name}'")
                        portal_svca.delete()
                else:
                    # Portal records without UID are new and should be created in K8S
                    logger.debug(f"Service account record '{portal_svca.namespace.name}:{portal_svca.name}' has no UID, creating it in the cluster ...")
                    portal_svca.create_in_cluster()
            return True
        except Exception as e:
            logger.exception(f"Syncing new portal namespaces into the cluster failed.")
            return False


    def create_in_cluster(self):
        """
        Creates a Kubernetes cluster service account based on an existing KubernetesServiceAccount object.
        """
        logger.debug(f"Creating service account '{self.namespace.name}:{self.name}' in cluster ...")
        try:
            created_k8s_svca = api.create_k8s_svca(namespace=self.namespace.name, name=self.name)
            self.uid = created_k8s_svca.metadata.uid
            self.save()
            return True
        except Exception as e:
            logger.exception(f"Creation of portal service account in cluster failed.")
            return False




