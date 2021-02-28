from django.conf import settings
from django.db import models
from django.db.models import Count
from kubeportal.k8s import kubernetes_api as api
import logging
import re

from kubeportal.k8s.kubernetes_api import rbac_v1

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public', 'kube-node-lease']



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
        Returns a list of namespaces without a service account.
        """
        visible_namespaces = cls.objects.filter(visible=True)
        counted_service_accounts = visible_namespaces.annotate(Count('service_accounts'))
        return [ns for ns in counted_service_accounts if ns.service_accounts__count == 0]

    @classmethod
    def without_pods(cls):
        """
        Returns a list of namespaces without pods.
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

    @classmethod
    def create_missing_in_portal(cls):
        """
        Scans the Kubernetes cluster for namespaces that have no representation
        as KubernetesNamespace object, and creates the latter accordingly.
        """
        try:
            k8s_ns_list = api.get_namespaces()
            if k8s_ns_list:
                for k8s_ns in k8s_ns_list:
                    k8s_ns_name, k8s_ns_uid = k8s_ns.metadata.name, k8s_ns.metadata.uid
                    # First calling exists(), and creating it in case, is faster than get_or_create() 
                    # but may impose an extremely small danger of race conditions.
                    # We trade performance for reliability here. 
                    if not cls.objects.filter(name=k8s_ns_name, uid=k8s_ns_uid).exists():
                        logger.info(f"Found new Kubernetes namespace {k8s_ns_name}, creating record.")
                        new_obj = cls(name=k8s_ns_name, uid=k8s_ns_uid)
                        if k8s_ns_name in HIDDEN_NAMESPACES:
                            new_obj.visible = False
                        else:
                            new_obj.visible = True
                        new_obj.save()
            return  True
        except Exception as e:
            logger.exception(f"Syncing new cluster namespaces into the portal failed.")
            return False


    @classmethod
    def create_missing_in_cluster(cls):
        """
        Scans the portal database for namespaces that have no representation
        in the Kubernetes cluster, and creates the latter accordingly.
        """
        try:
            # Create a list of cluster namespace UIDs that already exist
            k8s_ns_uid_list = [k8s_ns.metadata.uid for k8s_ns in api.get_namespaces()]

            # Scan portal namespace entries
            for portal_ns in cls.objects.all():
                if portal_ns.uid:
                    # Portal namespace records with UID must be given in K8S, or they are stale und should be deleted
                    if portal_ns.uid not in k8s_ns_uid_list:
                        logger.warning(f"Removing stale portal record for Kubernetes namespace '{portal_ns.name}'")
                        portal_ns.delete()
                else:
                    # Portal namespace records without UID are new and should be created in K8S
                    logger.debug(f"Namespace record {portal_ns.name} has no UID, creating it in Kubernetes ...")
                    portal_ns.create_in_cluster() # ignore success, continue sync in any case
            return True
        except Exception as e:
            logger.exception(f"Syncing new portal namespaces into the cluster failed.")
            return False


    def create_in_cluster(self):
        """
        Creates a Kubernetes cluster namespace based on an existing KubernetesNamespace object.
        The namespace name in the portal database is sanitized, K8S only allows DNS names for namespaces.
        UID and role bindings are set accordingly, so all the source object needs is a name.
        """
        logger.debug(f"Creating namespace '{self.name}' in cluster ...")
        try:
            sanitized_name = re.sub('[^a-zA-Z0-9]', '', self.name).lower()
            if sanitized_name != self.name:
                logger.warning(
                    f"Given name '{self.name}' for Kubernetes namespace is invalid, replacing it with '{sanitized_name}'")
                if sanitized_name not in KubernetesNamespace.objects.all():
                    self.name = sanitized_name
                else:
                    logger.error(
                        f"Could not create namespace in the cluster, sanitized name '{sanitized_name}' already exists.")
                    return False

            created_k8s_ns = api.create_k8s_ns(sanitized_name)
            self.uid = created_k8s_ns.metadata.uid
            self.save()
            return api.check_role_bindings(self)
        except Exception as e:
            logger.exception(f"Creation of portal namespace in cluster failed.")
            return False


    @classmethod
    def create_or_get(cls, k8s_ns_name):
        """
        Returns a newly created KubernetesNamespace object with the given name,
        assuming that it does not exist so far.

        When the namespace already exists, this object is returned instead.
        In any case, it is ensured that the cluster is in sync accordingly.
        """
        if cls.objects.filter(name=k8s_ns_name).exists():
            return cls.objects.get(name=k8s_ns_name)
        else:
            new_ns = cls(name=k8s_ns_name)
            if new_ns.create_in_cluster():
                # make sure that new default service account is synced
                from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount
                KubernetesServiceAccount.create_missing_in_portal()
                return new_ns
            else:
                return None


    @classmethod
    def get_or_sync(cls, k8s_ns_name):
        """
        Returns a KubernetesNamespace object with the given namespace name.
        When the object does not exist, it is assumed that the namespace only exists in the
        cluster so far, and that a sync is needed.
        """
        try:
            return cls.objects.get(name=k8s_ns_name)
        except cls.DoesNotExist:
            logger.debug(f"Could not find namespace {k8s_ns_name} in portal, triggering sync before next attempt.")
            cls.create_missing_in_portal()
            return cls.objects.get(name=k8s_ns_name)
        except cls.MultipleObjectsReturned:
            # We saw that happen in practice, reasons are still unclear.
            logger.error(f"Portal database entries for namespace {k8s_ns_name} are duplicated. Deleting all but the oldest one...")
            while cls.objects.filter(name=k8s_ns_name).count() > 1:
                candidate = cls.objects.filter(name=k8s_ns_name).order_by('-pk')[0]
                logger.error(f"Deleting record {candidate.pk}. Impacted service accounts: {candidate.service_accounts}")
                candidate.delete()
            return cls.objects.get(name=k8s_ns_name)
