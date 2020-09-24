'''
    Synchronization between Kubernetes API server and portal database.

    The API server is the master data source, the portal just mirrors it.
    The only exception are newly created records in the portal, which should
    lead to according resource creation in in API server.

    Kubeportal will never delete resources in Kubernetes, so there is no code
    and no UI for that. Admins should perform deletion operation directly
    in Kubernetes, e.g. through kubectl, and sync KubePortal afterwards.
'''

from django.conf import settings
from kubernetes import client
from . import utils
from base64 import b64decode

import logging

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


core_v1, rbac_v1 = utils.load_config()


def create_k8s_ns(name, core_v1):
    logger.info(
        "Creating Kubernetes namespace '{0}'".format(name))
    try:
        k8s_ns = client.V1Namespace(
            api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespace(k8s_ns)
    except client.rest.ApiException as e:
        # Race condition or earlier sync error - the K8S namespace is already there
        if e.status == 409:
            logger.warning("Tried to create already existing Kubernetes namespace {}. Skipping the creation and using the existing one.".format(name))
        else:
            raise e
    return core_v1.read_namespace(name=name)


def delete_k8s_ns(name, core_v1):
    if utils.is_minikube():
        logger.info(
            "Deleting Kubernetes namespace '{0}'".format(name))
        core_v1.delete_namespace(name)
    else:
        logger.error("K8S namespace deletion not allowed in production clusters")


def get_namespaces():
    '''
    Returns the list of cluster namespaces.
    '''
    try:
        return core_v1.list_namespace().items
    except Exception:
        logger.exception("Error while fetching namespaces from Kubernetes")
        return None


def get_service_accounts():
    '''
    Returns the list of service accounts.
    '''
    try:
        return core_v1.list_service_account_for_all_namespaces().items
    except Exception:
        logger.exception("Error while fetching service accounts from Kubernetes")
        return None


def get_pods():
    try:
        return core_v1.list_pod_for_all_namespaces().items
    except Exception as e:
        logger.error("Exception: {0}".format(e))
        return None


def get_token(kubeportal_service_account):
    service_account = core_v1.read_namespaced_service_account(
        name=kubeportal_service_account.name,
        namespace=kubeportal_service_account.namespace.name)
    secret_name = service_account.secrets[0].name
    secret = core_v1.read_namespaced_secret(
        name=secret_name, namespace=kubeportal_service_account.namespace.name)
    encoded_token = secret.data['token']
    return b64decode(encoded_token).decode()

def get_apiserver():
    if settings.API_SERVER_EXTERNAL is None:
        return core_v1.api_client.configuration.host
    else:
        return settings.API_SERVER_EXTERNAL

def get_kubernetes_version():
    pods = core_v1.list_namespaced_pod("kube-system").items
    for pod in pods:
        for container in pod.spec.containers:
            if 'kube-apiserver' in container.image:
                return container.image.split(":")[1]
    logger.error(f"Kubernetes version not identifiable, list of pods in 'kube-system': {pods}.")
    return None


def get_number_of_pods():
    return len(core_v1.list_pod_for_all_namespaces().items)


def get_number_of_nodes():
    return len(core_v1.list_node().items)


def get_number_of_cpus():
    nodes = core_v1.list_node().items
    return sum([int(node.status.capacity['cpu']) for node in nodes])


def get_memory_sum():
    nodes = core_v1.list_node().items
    mems = [int(node.status.capacity['memory'][:-2]) for node in nodes]
    return sum(mems) / 1000000  # in GiBytes


def get_number_of_volumes():
    return len(core_v1.list_persistent_volume().items)



