'''
    Synchronization between Kubernetes API server and portal database.

    The API server is the master data source, the portal just mirrors it.
    The only exception are newly created records in the portal, which should
    lead to according resource creation in in API server.

    Kubeportal will never delete resources in Kubernetes, so there is no code
    and no UI for that. Admins should perform deletion operation directly
    in Kubernetes, e.g. through kubectl, and sync KubePortal afterwards.
'''

from django.contrib import messages
from django.conf import settings
from kubernetes import client, config
from base64 import b64decode
import json
import logging

from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount

logger = logging.getLogger('KubePortal')


HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


def _sync_namespaces(request, core_v1, rbac_v1):
    # K8S namespaces -> portal namespaces
    success_count_pull = 0
    k8s_ns_list = None
    try:
        k8s_ns_list = core_v1.list_namespace()
    except Exception as e:
        logger.error("Exception: {0}".format(e))
        messages.error(request, "Sync failed, error while fetching list of namespaces: {0}.".format(e))
        return
    k8s_ns_uids = []
    for k8s_ns in k8s_ns_list.items:
        try:
            k8s_ns_name = k8s_ns.metadata.name
            k8s_ns_uid = k8s_ns.metadata.uid
            # remember for later use
            k8s_ns_uids.append(k8s_ns_uid)
            portal_ns, created = KubernetesNamespace.objects.get_or_create(
                name=k8s_ns_name, uid=k8s_ns_uid)
            if created:
                # Create missing namespace record
                logger.info(
                    "Creating record for Kubernetes namespace '{0}'".format(k8s_ns_name))
                if k8s_ns_name in HIDDEN_NAMESPACES:
                    portal_ns.visible = False
                else:
                    portal_ns.visible = True
                portal_ns.save()
                messages.info(request,
                              "Found new Kubernetes namespace '{0}'.".format(k8s_ns_name))
            else:
                # No action needed
                logger.debug(
                    "Found existing record for Kubernetes namespace '{0}'".format(k8s_ns_name))
                success_count_pull += 1
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            messages.error(request, "Sync from Kubernetes for namespace {0} failed: {1}.".format(k8s_ns_name, e))

    # portal namespaces -> K8S namespaces
    success_count_push = 0
    for portal_ns in KubernetesNamespace.objects.all():
        try:
            if portal_ns.uid:
                # Portal namespace records with UID must be given in K8S, or they are
                # stale und should be deleted
                if portal_ns.uid in k8s_ns_uids:
                    # No action needed
                    logger.debug(
                        "Found existing Kubernetes namespace for record '{0}'".format(portal_ns.name))
                    success_count_push += 1
                else:
                    # Remove stale namespace record
                    logger.warning(
                        "Removing stale record for Kubernetes namespace '{0}'".format(portal_ns.name))
                    portal_ns.delete()
                    messages.info(
                        request, "Namespace '{0}' no longer exists in Kubernetes and was removed.".format(portal_ns.name))
            else:
                # Portal namespaces without UID are new and should be created in K8S
                logger.info(
                    "Creating Kubernetes namespace '{0}'".format(portal_ns.name))
                k8s_ns = client.V1Namespace(
                    api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=portal_ns.name))
                core_v1.create_namespace(k8s_ns)
                # Fetch UID and store it in portal record
                created_k8s_ns = core_v1.read_namespace(name=portal_ns.name)
                portal_ns.uid = created_k8s_ns.metadata.uid
                portal_ns.save()
                messages.success(
                    request, "Created namespace '{0}' in Kubernetes.".format(portal_ns.name))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            messages.error(request, "Sync to Kubernetes for namespace {0} failed: {1}.".format(portal_ns, e))

    if success_count_push == success_count_pull:
        messages.success(
            request, "All valid namespaces are in sync.")

    # check role bindings of namespaces
    # We only consider visible namespaces here, to prevent hitting
    # special namespaces and giving them (most likely unneccessary)
    # additional role bindings
    for portal_ns in KubernetesNamespace.objects.filter(visible=True):
        # Get role bindings in the current namespace
        try:
            rolebindings = rbac_v1.list_namespaced_role_binding(portal_ns.name)
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            messages.error(request, "Could not fetch role bindings for namespace '{0}': {1}.".format(portal_ns, e))
            continue
        # Get all cluster roles this namespace is currently bound to
        clusterroles_active = [rolebinding.role_ref.name for rolebinding in rolebindings.items if rolebinding.role_ref.kind == 'ClusterRole']
        logger.debug("Namespace '{0}' is bound to cluster roles {1}".format(portal_ns, clusterroles_active))
        # Check list of default cluster roles from settings
        for clusterrole in settings.NAMESPACE_CLUSTERROLES:
            if clusterrole not in clusterroles_active:
                try:
                    logger.info("Namespace '{0}' is not bound to cluster role '{1}', fixing this ...".format(portal_ns, clusterrole))
                    role_ref = client.V1RoleRef(name=clusterrole, kind="ClusterRole", api_group="rbac.authorization.k8s.io")
                    # Subject for the cluster role are all service accounts in the namespace
                    subject = client.V1Subject(name="system:serviceaccounts:" + portal_ns.name, kind="Group", api_group="rbac.authorization.k8s.io")
                    metadata = client.V1ObjectMeta(name=clusterrole)
                    new_rolebinding = client.V1RoleBinding(role_ref=role_ref, metadata=metadata, subjects=[subject, ])
                    rbac_v1.create_namespaced_role_binding(portal_ns.name, new_rolebinding)
                except Exception as e:
                    logger.exception(e)
                    messages.error(request, "Could not create binding of namespace '{0}' to cluster role '{1}': {2}.".format(portal_ns.name, clusterrole, e))
                    continue


def _sync_svcaccounts(request, v1):
    # K8S svc accounts -> portal svc accounts
    success_count_pull = 0
    ignored_missing_ns = []
    k8s_svca_uids = []
    k8s_svca_list = None
    try:
        k8s_svca_list = v1.list_service_account_for_all_namespaces()
    except Exception as e:
        logger.error("Exception: {0}".format(e))
        messages.error(request, "Sync failed, error while fetching list of service accounts: {0}.".format(e))
        return
    for k8s_svca in k8s_svca_list.items:
        try:
            # remember for later use
            k8s_svca_uids.append(k8s_svca.metadata.uid)
            # Not finding the namespace record for this namespace name
            # means inconsistency - re-sync is needed anyway, so stopping
            # here is fine
            try:
                portal_ns = KubernetesNamespace.objects.get(
                    name=k8s_svca.metadata.namespace)
            except Exception:
                logger.warning("Skipping Kubernetes service account {0}:{1}, namespace does not exist.".format(
                    k8s_svca.metadata.namespace, k8s_svca.metadata.name))
                ignored_missing_ns.append(
                    (k8s_svca.metadata.namespace, k8s_svca.metadata.name))
                continue
            portal_svca, created = KubernetesServiceAccount.objects.get_or_create(
                name=k8s_svca.metadata.name, uid=k8s_svca.metadata.uid, namespace=portal_ns)
            if created:
                # Create missing service account record
                logger.info("Creating record for Kubernetes service account '{0}:{1}'".format(
                    k8s_svca.metadata.namespace, k8s_svca.metadata.name))
                portal_svca.save()
                messages.info(request,
                              "Found new Kubernetes service account '{0}:{1}'.".format(k8s_svca.metadata.namespace, k8s_svca.metadata.name))
            else:
                # No action needed
                logger.info("Found existing record for Kubernetes service account '{0}:{1}'".format(
                    k8s_svca.metadata.namespace, k8s_svca.metadata.name))
                success_count_pull += 1
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            messages.error(request, "Sync from Kubernetes for service account {0} failed: {1}.".format(k8s_svca.metadata.name, e))

    if len(ignored_missing_ns) > 0:
        names = ["{0}:{1}".format(a, b)
                 for a, b in ignored_missing_ns]
        messages.warning(
            request, "Skipping service accounts with non-existent namespaces: {0}".format(names))

    # portal service accounts -> K8S service accounts
    success_count_push = 0
    for portal_svca in KubernetesServiceAccount.objects.all():
        try:
            portal_ns = portal_svca.namespace
            if portal_svca.uid:
                # Portal service account records with UID must be given in K8S, or they are
                # stale und should be deleted
                if portal_svca.uid in k8s_svca_uids:
                    # No action needed
                    logger.info(
                        "Found existing Kubernetes service account for record '{0}:{1}'".format(portal_ns.name, portal_svca.name))
                    success_count_push += 1
                else:
                    # Remove stale record
                    logger.warning(
                        "Removing stale record for Kubernetes service account '{0}:{1}'".format(portal_ns.name, portal_svca.name))
                    portal_svca.delete()
                    messages.info(request, "Service account '{0}:{1}' no longer exists in Kubernetes and was removed.".format(
                        portal_ns.name, portal_svca.name))
            else:
                # Portal service accounts without UID are new and should be created in K8S
                logger.info(
                    "Creating Kubernetes service account '{0}:{1}'".format(portal_ns.name, portal_svca.name))
                k8s_svca = client.V1ServiceAccount(
                    api_version="v1", kind="ServiceAccount", metadata=client.V1ObjectMeta(name=portal_svca.name))
                v1.create_namespaced_service_account(
                    namespace=portal_ns.name, body=k8s_svca)
                # Fetch UID and store it in portal record
                created_k8s_svca = v1.read_namespaced_service_account(
                    name=portal_svca.name, namespace=portal_ns.name)
                portal_svca.uid = created_k8s_svca.metadata.uid
                portal_svca.save()
                messages.success(request, "Created service account '{0}:{1}' in Kubernetes.".format(
                    portal_ns.name, portal_svca.name))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            messages.error(request, "Sync to Kubernetes for service account {0} failed: {1}.".format(portal_ns.name, e))

    if success_count_push == success_count_pull:
        messages.success(
            request, "All valid service accounts are in sync.")


def _load_config():
    try:
        # Production mode
        config.load_incluster_config()
        return
    except Exception:
        # Dev mode
        pass
    # Let it fail without being in a nested exception handling
    config.load_kube_config()


def sync(request):
    '''
    Synchronizes the local shallow copy of Kubernetes data.
    Returns True on success.
    '''
    _load_config()
    try:
        core_v1 = client.CoreV1Api()
        rbac_v1 = client.RbacAuthorizationV1Api()
        _sync_namespaces(request, core_v1, rbac_v1)
        _sync_svcaccounts(request, core_v1)
        return True
    except client.rest.ApiException as e:
        msg = json.loads(e.body)['message']
        logger.error(
            "API server exception during synchronization: {0}".format(msg))
        messages.error(
            request, "Kubernetes returned an error during synchronization: {0}".format(msg))
        return False


def get_token(kubeportal_service_account):
    _load_config()
    v1 = client.CoreV1Api()
    service_account = v1.read_namespaced_service_account(
        name=kubeportal_service_account.name,
        namespace=kubeportal_service_account.namespace.name)
    secret_name = service_account.secrets[0].name
    secret = v1.read_namespaced_secret(
        name=secret_name, namespace=kubeportal_service_account.namespace.name)
    encoded_token = secret.data['token']
    return b64decode(encoded_token).decode()


def get_apiserver():
    _load_config()
    v1 = client.CoreV1Api()
    return v1.api_client.configuration.host


def get_stats():
    _load_config()
    v1 = client.CoreV1Api()
    result = {}
    result['apiserver'] = v1.api_client.configuration.host
    apiserver_image = v1.list_namespaced_pod("kube-system", label_selector="component=kube-apiserver").items[0].spec.containers[0].image.split(":")[1]
    result['k8sversion'] = apiserver_image
    result['numberofpods'] = len(v1.list_pod_for_all_namespaces().items)
    nodes = v1.list_node().items
    result['numberofnodes'] = len(nodes)
    cpus = [int(node.status.capacity['cpu']) for node in nodes]
    result['cpusum'] = sum(cpus)
    mems = [int(node.status.capacity['memory'][:-2]) for node in nodes]
    result['memsum'] = sum(mems)/1000000 # in GiBytes
    result['numberofvolumes'] = len(v1.list_persistent_volume().items)
    return result
