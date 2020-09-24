from django.conf import settings
from django.contrib import messages

from kubeportal.models import KubernetesNamespace
from kubernetes import client
from kubeportal.k8s.utils import load_config, error_log
import logging
import re

logger = logging.getLogger('KubePortal')
HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


def check_role_bindings_of_namespaces(request, rbac_v1):
    """
    We only consider visible namespaces here, to prevent hitting special namespaces and giving them
    (most likely unneccessary) additional role bindings
    """

    for portal_ns in KubernetesNamespace.objects.filter(visible=True):
        # Get role bindings in the current namespace
        try:
            rolebindings = rbac_v1.list_namespaced_role_binding(portal_ns.name)
        except Exception as e:
            error_log(request, e, portal_ns, "Could not fetch role bindings for namespace '{}': {}.")
            continue
        # Get all cluster roles this namespace is currently bound to
        clusterroles_active = [
            rolebinding.role_ref.name for rolebinding in rolebindings.items if
            rolebinding.role_ref.kind == 'ClusterRole']
        logger.debug("Namespace '{0}' is bound to cluster roles {1}".format(
            portal_ns, clusterroles_active))
        # Check list of default cluster roles from settings
        for clusterrole in settings.NAMESPACE_CLUSTERROLES:
            if clusterrole not in clusterroles_active:
                try:
                    logger.info("Namespace '{0}' is not bound to cluster role '{1}', fixing this ...".format(
                        portal_ns, clusterrole))
                    role_ref = client.V1RoleRef(
                        name=clusterrole, kind="ClusterRole", api_group="rbac.authorization.k8s.io")
                    # Subject for the cluster role are all service accounts in the namespace
                    subject = client.V1Subject(
                        name="system:serviceaccounts:" + portal_ns.name, kind="Group",
                        api_group="rbac.authorization.k8s.io")
                    metadata = client.V1ObjectMeta(name=clusterrole)
                    new_rolebinding = client.V1RoleBinding(
                        role_ref=role_ref, metadata=metadata, subjects=[subject, ])
                    rbac_v1.create_namespaced_role_binding(
                        portal_ns.name, new_rolebinding)
                except Exception as e:
                    error_log(request, e, (portal_ns.name, clusterrole),
                                   "Could not create binding of namespace '{}' to cluster role '{}': {}.")
                    continue


def add_namespace_to_kubeportal(k8s_ns_name, portal_ns, request):
    # Create missing namespace record
    logger.info(
        f"Creating record for Kubernetes namespace '{k8s_ns_name}'.")
    if k8s_ns_name in HIDDEN_NAMESPACES:
        portal_ns.visible = False
    else:
        portal_ns.visible = True
    portal_ns.save()
    messages.info(request, f"Found new Kubernetes namespace '{k8s_ns_name}'.")


def add_namespace_to_kubernetes(portal_ns, request, core_v1, api):
    logger.debug(f"Namespace record {portal_ns.name} has no UID, creating it in Kubernetes ...")
    # Sanitize name, K8S only allows DNS names for namespaces
    sanitized_name = re.sub('[^a-zA-Z0-9]', '', portal_ns.name).lower()
    if sanitized_name != portal_ns.name:
        logger.warning(
            "Given name '{}' for new Kubernetes namespace is invalid, replacing it with '{}'".format(portal_ns.name,
                                                                                                     sanitized_name))
        messages.warning(request,
                         "Given name '{}' for new Kubernetes namespace was invalid, chosen name is now '{}'".format(
                             portal_ns.name, sanitized_name))
        # TODO: May already exist?
        portal_ns.name = sanitized_name
        portal_ns.save()
    created_k8s_ns = api.create_k8s_ns(portal_ns.name, core_v1)
    portal_ns.uid = created_k8s_ns.metadata.uid
    portal_ns.save()
    messages.success(request, "Created namespace '{0}' in Kubernetes.".format(portal_ns.name))


def delete_namespace_in_kubernetes(request, portal_ns):
    logger.warning(
        "Removing stale record for Kubernetes namespace '{0}'".format(portal_ns.name))
    portal_ns.delete()
    messages.info(
        request, "Namespace '{0}' no longer exists in Kubernetes and was removed.".format(portal_ns.name))


def check_if_portal_ns_exists_in_k8s(portal_ns, request, k8s_ns_uids, success_count_push):
    if portal_ns.uid in k8s_ns_uids:
        # No action needed
        logger.debug(f"Found existing Kubernetes namespace for record '{portal_ns.name}'")
        success_count_push += 1
    else:
        # Remove stale namespace record
        delete_namespace_in_kubernetes(portal_ns, request)