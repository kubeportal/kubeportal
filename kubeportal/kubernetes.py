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
from kubernetes import client, config
from base64 import b64decode
import json
import logging

from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount

logger = logging.getLogger('KubePortal')


def _sync_namespaces(request, v1):
    try:
        # K8S namespaces -> portal namespaces
        success_count_pull = 0
        k8s_ns_list = v1.list_namespace()
        k8s_ns_uids = []
        for k8s_ns in k8s_ns_list.items:
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
                portal_ns.save()
                messages.info(request,
                              "Found new Kubernetes namespace '{0}'.".format(k8s_ns_name))
            else:
                # No action needed
                logger.debug(
                    "Found existing record for Kubernetes namespace '{0}'".format(k8s_ns_name))
                success_count_pull += 1

        # portal namespaces -> K8S namespaces
        success_count_push = 0
        for portal_ns in KubernetesNamespace.objects.all():
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
                v1.create_namespace(k8s_ns)
                # Fetch UID and store it in portal record
                created_k8s_ns = v1.read_namespace(name=portal_ns.name)
                portal_ns.uid = created_k8s_ns.metadata.uid
                portal_ns.save()
                messages.success(
                    request, "Created namespace '{0}' in Kubernetes.".format(portal_ns.name))

        if success_count_push == success_count_pull:
            messages.success(
                request, "All valid namespaces are in sync.")

    except Exception as e:
        logger.error("Exception: {0}".format(e))
        messages.error(
            request, "Error while synchronizing namespaces: {0}.".format(e))


def _sync_svcaccounts(request, v1):
    try:
        # K8S svc accounts -> portal svc accounts
        success_count_pull = 0
        ignored_missing_ns = []
        k8s_svca_uids = []
        k8s_svca_list = v1.list_service_account_for_all_namespaces()
        for k8s_svca in k8s_svca_list.items:
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
        if ignored_missing_ns is not []:
            names = ["{0}:{1}".format(a, b)
                     for a, b in ignored_missing_ns]
            messages.warning(
                request, "Skipping service accounts with non-existent namespaces: {0}".format(names))

        # portal service accounts -> K8S service accounts
        success_count_push = 0
        for portal_svca in KubernetesServiceAccount.objects.all():
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

        if success_count_push == success_count_pull:
            messages.success(
                request, "All valid service accounts are in sync.")

    except Exception as e:
        logger.error("Exception: {0}".format(e))
        messages.error(
            request, "Error while synchronizing service accounts: {0}.".format(e))


def sync(request):
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        _sync_namespaces(request, v1)
        _sync_svcaccounts(request, v1)
    except client.rest.ApiException as e:
        msg = json.loads(e.body)['message']
        logger.error(
            "API server exception during synchronization: {0}".format(msg))
        messages.error(
            request, "Kubernetes returned an error during synchronization: {0}".format(msg))


def get_token(kubeportal_service_account):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    service_account = v1.read_namespaced_service_account(
        name=kubeportal_service_account.name,
        namespace=kubeportal_service_account.namespace.name)
    secret_name = service_account.secrets[0].name
    secret = v1.read_namespaced_secret(
        name=secret_name, namespace=kubeportal_service_account.namespace.name)
    encoded_token = secret.data['token']
    return b64decode(encoded_token).decode()
