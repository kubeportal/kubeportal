from django.contrib import messages
from kubernetes import client
import logging

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.k8s.kubernetes_api import core_v1


logger = logging.getLogger('KubePortal')


def get_portal_ns_using_k8s_ns(k8s_svca, ignored_missing_ns):
    try:
        portal_ns = KubernetesNamespace.objects.get(name=k8s_svca.metadata.namespace)
    except KubernetesNamespace.MultipleObjectsReturned:
        logger.error(f"Portal database entries for namespace {k8s_svca.metadata.namespace} are duplicated. Deleting all but the oldest one...")
        while KubernetesNamespace.objects.filter(name=k8s_svca.metadata.namespace).count() > 1:
            candidate = KubernetesNamespace.objects.filter(name=k8s_svca.metadata.namespace).order_by('-pk')[0]
            logger.error(f"Deleting record {candidate.pk}. Impacted service accounts: {candidate.service_accounts}")
            candidate.delete()
        portal_ns = KubernetesNamespace.objects.get(name=k8s_svca.metadata.namespace)

    if portal_ns is None:
        logger.warning("Skipping Kubernetes service account {0}:{1}, namespace does not exist.".format(
            k8s_svca.metadata.namespace, k8s_svca.metadata.name))
        ignored_missing_ns.append(
            (k8s_svca.metadata.namespace, k8s_svca.metadata.name))
        return None
    return portal_ns


def add_svca_to_kubeportal(request, k8s_svca, portal_svca):
    # Create missing service account record
    logger.info("Creating record for Kubernetes service account '{0}:{1}'".format(
        k8s_svca.metadata.namespace, k8s_svca.metadata.name))
    portal_svca.save()
    messages.info(request, "Found new Kubernetes service account '{0}:{1}'.".format(
        k8s_svca.metadata.namespace, k8s_svca.metadata.name))


def add_svca_to_kubernetes(request, portal_svca, portal_ns):
    logger.info(
        "Creating Kubernetes service account '{0}:{1}'".format(portal_ns.name, portal_svca.name))
    k8s_svca = client.V1ServiceAccount(
        api_version="v1", kind="ServiceAccount", metadata=client.V1ObjectMeta(name=portal_svca.name))
    core_v1.create_namespaced_service_account(
        namespace=portal_ns.name, body=k8s_svca)
    # Fetch UID and store it in portal record
    created_k8s_svca = core_v1.read_namespaced_service_account(
        name=portal_svca.name, namespace=portal_ns.name)
    portal_svca.uid = created_k8s_svca.metadata.uid
    portal_svca.save()
    messages.success(request, "Created service account '{0}:{1}' in Kubernetes.".format(
        portal_ns.name, portal_svca.name))