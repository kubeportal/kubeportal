"""
    Synchronization between Kubernetes API server and portal data

    The API server is the master data source, the portal just mirrors it.
    The only exception are newly created records in the portal, which should
    lead to according resource creation in in API server.

    Kubeportal will never delete resources in Kubernetes, so there is no code
    and no UI for that. Admins should perform deletion operation directly
    in Kubernetes, e.g. through kubectl, and sync KubePortal afterwards.
"""

import json
import logging

from django.contrib import messages
from kubernetes import client

from kubeportal.k8s import kubernetes_api as api
from kubeportal.k8s import ns_sync_utils as ns_utils
from kubeportal.k8s import svca_sync_utils as svca_utils
from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount

logger = logging.getLogger('KubePortal')

k8s_ns_uids = []


def _sync_svcaccounts(request):
    #################################################
    # K8S svc accounts -> portal svc accounts
    #################################################
    success_count_pull = 0
    success_count_push = 0
    ignored_missing_ns = []
    k8s_svca_uids = []

    k8s_svca_list = api.get_service_accounts()
    if k8s_svca_list:
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
            logger.exception(f"Sync from portal to Kubernetes for service account '{portal_svca.name}' failed.")

    if success_count_push == success_count_pull:
        messages.success(request, "All valid service accounts are in sync.")


def sync(request):
    '''
    Synchronizes the local shallow copy of Kubernetes data.
    Returns True on success.
    '''
    try:
        KubernetesNamespace.create_missing_in_portal()
        KubernetesNamespace.create_missing_in_cluster()
        _sync_svcaccounts(request)
        return True
    except client.rest.ApiException as e:
        msg = json.loads(e.body)['message']
        logger.error(
            "API server exception during synchronization: {0}".format(msg))
        messages.error(
            request, "Kubernetes returned an error during synchronization: {0}".format(msg))
        return False
