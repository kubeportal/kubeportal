'''
    Synchronization between Kubernetes API server and portal data

    The API server is the master data source, the portal just mirrors it.
    The only exception are newly created records in the portal, which should
    lead to according resource creation in in API server.

    Kubeportal will never delete resources in Kubernetes, so there is no code
    and no UI for that. Admins should perform deletion operation directly
    in Kubernetes, e.g. through kubectl, and sync KubePortal afterwards.
'''

from django.contrib import messages
from kubernetes import client
from .utils import load_config, error_log
from . import ns_sync_utils as ns_utils
from . import svca_sync_utils as svca_utils
from . import kubernetes_api as api

import json
import logging

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount


logger = logging.getLogger('KubePortal')

core_v1, rbac_v1 = load_config()

k8s_ns_uids = []


def _sync_namespaces(request):
    #################################################
    # K8S namespaces -> portal namespaces
    #################################################
    success_count_push = 0
    success_count_pull = 0

    try:
        k8s_ns_list = core_v1.list_namespace()
    except Exception as e:
        error_log(request, e, None, 'Sync failed, error while fetching list of namespaces: {e}')
        return

    for k8s_ns in k8s_ns_list.items:
        try:
            k8s_ns_name, k8s_ns_uid = k8s_ns.metadata.name, k8s_ns.metadata.uid
            # remember for later use
            k8s_ns_uids.append(k8s_ns_uid)

            portal_ns, created = KubernetesNamespace.objects.get_or_create(
                name=k8s_ns_name, uid=k8s_ns_uid)
            if created:
                ns_utils.add_namespace_to_kubeportal(k8s_ns_name, portal_ns, request)
            else:
                # No action needed
                logger.debug(f"Found existing record for Kubernetes namespace '{k8s_ns_name}'")
                success_count_pull += 1
        except Exception as e:
            error_log(request, e, k8s_ns.metadata.name, 'Sync from Kubernetes for namespace {} failed: {}.')

    #################################################
    # portal namespaces -> K8S namespaces
    #################################################
    for portal_ns in KubernetesNamespace.objects.all():
        try:
            if portal_ns.uid:
                # Portal namespace records with UID must be given in K8S, or they are stale und should be deleted
                if portal_ns.uid in k8s_ns_uids:
                    # No action needed
                    logger.debug(f"Found existing Kubernetes namespace for record '{portal_ns.name}'")
                    success_count_push += 1
                else:
                    # Remove stale namespace record
                    ns_utils.delete_namespace_in_kubernetes(request, portal_ns)
            else:
                # Portal namespaces without UID are new and should be created in K8S
                ns_utils.add_namespace_to_kubernetes(portal_ns, request, core_v1, api)
        except Exception as e:
            error_log(request, e, portal_ns, 'Sync to Kubernetes for namespace {} failed: {}."')

    if success_count_push == success_count_pull:
        messages.success(request, "All valid namespaces are in sync.")

    ns_utils.check_role_bindings_of_namespaces(request, rbac_v1)


def _sync_svcaccounts(request):
    #################################################
    # K8S svc accounts -> portal svc accounts
    #################################################
    success_count_pull = 0
    success_count_push = 0
    ignored_missing_ns = []
    k8s_svca_uids = []

    try:
        k8s_svca_list = core_v1.list_service_account_for_all_namespaces()
    except Exception as e:
        error_log(request, e, None, "Sync failed, error while fetching list of service accounts: {}.")
        return

    for k8s_svca in k8s_svca_list.items:
        try:
            # remember for later use
            '''
            Not finding the namespace record for this namespace name means inconsistency 
            - re-sync is needed anyway, so stopping here is fine
            '''
            k8s_svca_uids.append(k8s_svca.metadata.uid)
            portal_ns = svca_utils.get_portal_ns_using_k8s_ns(k8s_svca, ignored_missing_ns)

            portal_svca, created = KubernetesServiceAccount.objects.get_or_create(
                name=k8s_svca.metadata.name, uid=k8s_svca.metadata.uid, namespace=portal_ns)

            if created:
                svca_utils.add_svca_to_kubeportal(request, k8s_svca, portal_svca)
            else:
                # No action needed
                logger.info("Found existing record for Kubernetes service account '{0}:{1}'".format(
                    k8s_svca.metadata.namespace, k8s_svca.metadata.name))
                success_count_pull += 1
        except Exception as e:
            error_log(request, e, k8s_svca.metadata.name, 'Sync from Kubernetes for service account {} failed: {}."')

    if len(ignored_missing_ns) > 0:
        names = ["{0}:{1}".format(a, b)
                 for a, b in ignored_missing_ns]
        messages.warning(
            request, "Skipping service accounts with non-existent namespaces: {0}".format(names))

    #################################################
    # portal service accounts -> K8S service accounts
    #################################################
    for portal_svca in KubernetesServiceAccount.objects.all():
        try:
            portal_ns = portal_svca.namespace
            if portal_svca.uid:
                # Portal service account records with UID must be given in K8S, or they are
                # stale und should be deleted
                if portal_svca.uid in k8s_svca_uids:
                    # No action needed
                    logger.info(
                        "Found existing Kubernetes service account for record '{0}:{1}'".format(portal_ns.name,
                                                                                                portal_svca.name))
                    success_count_push += 1
                else:
                    # Remove stale record
                    logger.warning(
                        "Removing stale record for Kubernetes service account '{0}:{1}'".format(portal_ns.name,
                                                                                                portal_svca.name))
                    portal_svca.delete()
                    messages.info(request,
                                  "Service account '{0}:{1}' no longer exists in Kubernetes and was removed.".format(
                                      portal_ns.name, portal_svca.name))
            else:
                # Portal service accounts without UID are new and should be created in K8S
                svca_utils.add_svca_to_kubernetes(request, portal_svca, portal_ns, core_v1)
        except Exception as e:
            error_log(request, e, portal_svca.namespace, 'Sync to Kubernetes for service account {} failed: {}.')

    if success_count_push == success_count_pull:
        messages.success(request, "All valid service accounts are in sync.")


def sync(request):
    '''
    Synchronizes the local shallow copy of Kubernetes data.
    Returns True on success.
    '''
    try:
        _sync_namespaces(request)
        _sync_svcaccounts(request)
        return True
    except client.rest.ApiException as e:
        msg = json.loads(e.body)['message']
        logger.error(
            "API server exception during synchronization: {0}".format(msg))
        messages.error(
            request, "Kubernetes returned an error during synchronization: {0}".format(msg))
        return False
