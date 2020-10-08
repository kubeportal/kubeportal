from django.conf import settings
from django.contrib import messages

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubernetes import client
from kubeportal.k8s.utils import error_log
from kubeportal.k8s.kubernetes_api import rbac_v1
import logging
import re

logger = logging.getLogger('KubePortal')
HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


def check_role_bindings_of_namespaces(request):
    """
    We only consider visible namespaces here, to prevent hitting special namespaces and giving them
    (most likely unneccessary) additional role bindings
    """
    portal_ns_list = KubernetesNamespace.objects.filter(visible=True)
    for portal_ns in portal_ns_list:
        # Get role bindings in the current namespace
        try:
            rolebindings = rbac_v1.list_namespaced_role_binding(portal_ns.name).items
        except Exception as e:
            error_log(request, e, portal_ns, "Could not fetch role bindings for namespace '{}': {}.")
            continue
        # Get all cluster roles this namespace is currently bound to
        clusterroles_active = [rolebinding.role_ref.name for rolebinding in rolebindings if
                               rolebinding.role_ref.kind == 'ClusterRole']
        logger.debug(f"Namespace '{portal_ns}' is bound to cluster roles {clusterroles_active}")
        # Check list of default cluster roles from settings
        for clusterrole in settings.NAMESPACE_CLUSTERROLES:
            if clusterrole not in clusterroles_active:
                try:
                    logger.info(f"Namespace '{portal_ns}' is not bound to cluster role '{clusterrole}', fixing this ...")
                    _bind_namespace_to_cluster_role(clusterrole, portal_ns)
                except Exception as e:
                    error_log(request, e, (portal_ns.name, clusterrole),
                              "Could not create binding of namespace '{}' to cluster role '{}': {}.")
                    continue


def _bind_namespace_to_cluster_role(clusterrole, portal_ns):
    role_ref = client.V1RoleRef(name=clusterrole, kind="ClusterRole", api_group="rbac.authorization.k8s.io")
    # Subject for the cluster role are all service accounts in the namespace
    subject = client.V1Subject(name="system:serviceaccounts:" + portal_ns.name, kind="Group", api_group="rbac.authorization.k8s.io")
    metadata = client.V1ObjectMeta(name=clusterrole)
    new_rolebinding = client.V1RoleBinding(role_ref=role_ref, metadata=metadata, subjects=[subject, ])
    rbac_v1.create_namespaced_role_binding(portal_ns.name, new_rolebinding)


def add_namespace_to_kubeportal(k8s_ns_name, portal_ns, request):
    # Create missing namespace record
    logger.info(f"Creating record for Kubernetes namespace '{k8s_ns_name}'.")
    if k8s_ns_name in HIDDEN_NAMESPACES:
        portal_ns.visible = False
    else:
        portal_ns.visible = True
    portal_ns.save()
    messages.info(request, f"Found new Kubernetes namespace '{k8s_ns_name}'.")


def add_namespace_to_kubernetes(portal_ns, request, api):
    logger.debug(f"Namespace record {portal_ns.name} has no UID, creating it in Kubernetes ...")
    # Sanitize name, K8S only allows DNS names for namespaces
    sanitized_name = re.sub('[^a-zA-Z0-9]', '', portal_ns.name).lower()
    if sanitized_name != portal_ns.name:
        if not _try_create_ns_with_sanitized_name(request, portal_ns, sanitized_name):
            return
    created_k8s_ns = api.create_k8s_ns(sanitized_name)
    portal_ns.uid = created_k8s_ns.metadata.uid
    portal_ns.save()
    messages.success(request, "Created namespace '{0}' in Kubernetes.".format(sanitized_name))


def _try_create_ns_with_sanitized_name(request, portal_ns, sanitized_name):
    logger.warning(
        "Given name '{}' for new Kubernetes namespace is invalid, replacing it with '{}'".format(portal_ns.name,
                                                                                                 sanitized_name))
    messages.warning(request,
                     "Given name '{}' for new Kubernetes namespace was invalid, chosen name is now '{}'".format(
                         portal_ns.name, sanitized_name))
    if sanitized_name not in KubernetesNamespace.objects.all():
        portal_ns.name = sanitized_name
        portal_ns.save()
        return True
    else:
        logger.error(f"Sanitized name '{sanitized_name}' already exists in portal, could not be created in Kubernetes.")
        messages.error(request,
                       f"Sanitized name '{sanitized_name}' already exists in portal, could not be created in Kubernetes.")


def check_if_portal_ns_exists_in_k8s(request, portal_ns, k8s_ns_uids, success_count_push):
    # Portal namespace records with UID must be given in K8S, or they are stale und should be deleted
    if portal_ns.uid in k8s_ns_uids:
        # No action needed
        logger.debug(f"Found existing Kubernetes namespace for record '{portal_ns.name}'")
        success_count_push += 1
    else:
        # remove stale namespace from portal
        logger.warning(f"Removing stale record for Kubernetes namespace '{portal_ns.name}'")
        portal_ns.delete()
        messages.info(request,
                      f"Namespace '{portal_ns.name}' no longer exists in Kubernetes and was removed from portal.")
