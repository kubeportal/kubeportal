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
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount
from kubeportal.k8s.utils import load_config
from kubeportal.k8s import ns_sync_utils as ns_utils
from kubeportal.k8s import svca_sync_utils as svca_utils
from kubeportal.k8s import kubernetes_api as api

import json
import logging


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
        k8s_ns_list = api.get_namespaces()
    except Exception as e:
        logger.exception(f"Sync failed, error while fetching list of namespaces.")
        return

    for k8s_ns in k8s_ns_list:
        try:
            k8s_ns_name, k8s_ns_uid = k8s_ns.metadata.name, k8s_ns.metadata.uid
            # remember for later use
            k8s_ns_uids.append(k8s_ns_uid)

            portal_ns, created = KubernetesNamespace.objects.get_or_create(name=k8s_ns_name, uid=k8s_ns_uid)
            if created:
                ns_utils.add_namespace_to_kubeportal(k8s_ns_name, portal_ns, request)
            else:
                # No action needed
                logger.debug(f"Found existing record for Kubernetes namespace '{k8s_ns_name}'")
                success_count_pull += 1
        except Exception as e:
            logger.exception(f"Sync from Kubernetes to portal for namespace '{k8s_ns}' failed.")

    #################################################
    # portal namespaces -> K8S namespaces
    #################################################
    portal_ns_list = KubernetesNamespace.objects.all()
    for portal_ns in portal_ns_list:
        try:
            if portal_ns.uid:
                ns_utils.check_if_portal_ns_exists_in_k8s(request, portal_ns, k8s_ns_uids, success_count_push)
            else:
                # Portal namespaces without UID are new and should be created in K8S
                ns_utils.add_namespace_to_kubernetes(portal_ns, request, api)
        except Exception as e:
            logger.exception(f"Sync from portal to Kubernetes for namespace '{portal_ns}' failed.")

    if success_count_push == success_count_pull:
        messages.success(request, "All valid namespaces are in sync.")

    ns_utils.check_role_bindings_of_namespaces(request)


def _sync_svcaccounts(request):
    #################################################
    # K8S svc accounts -> portal svc accounts
    #################################################
    success_count_pull = 0
    success_count_push = 0
    ignored_missing_ns = []
    k8s_svca_uids = []

    try:
        k8s_svca_list = api.get_service_accounts()
    except Exception as e:
        logger.exception(f"Sync failed, error while fetching list of service accounts.")
        return

    for k8s_svca in k8s_svca_list:
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
            logger.exception(f"Sync from Kubernetes to portal for service account '{k8s_svca}' failed.")

    if len(ignored_missing_ns) > 0:
        names = ["{0}:{1}".format(a, b)
                 for a, b in ignored_missing_ns]
        messages.warning(
            request, "Skipping service accounts with non-existent namespaces: {0}".format(names))

    #################################################
    # portal service accounts -> K8S service accounts
    #################################################
    portal_svca_list = KubernetesServiceAccount.objects.all()
    for portal_svca in portal_svca_list:
        try:
            portal_ns = portal_svca.namespace
            if portal_svca.uid:
                # Portal service account records with UID must be given in K8S, or they are
                # stale und should be deleted
                if portal_svca.uid in k8s_svca_uids:
                    # No action needed
                    logger.info(
                        f"Found existing Kubernetes service account for record '{portal_ns.name}:{portal_svca.name}'")
                    success_count_push += 1
                else:
                    # Remove stale record from portal
                    logger.warning(
                        f"Removing stale record for Kubernetes service account '{portal_ns.name}:{portal_svca.name}'")
                    portal_svca.delete()
                    messages.info(request,
                                  f"Service account '{portal_ns.name}:{portal_svca.name}' no longer exists in portal and was removed.")
            else:
                # Portal service accounts without UID are new and should be created in K8S
                svca_utils.add_svca_to_kubernetes(request, portal_svca, portal_ns)
        except Exception as e:
            logger.exception(f"Sync from portal to Kubernetes for service account '{portal_svca}' failed.")

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
