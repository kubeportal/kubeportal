'''
    A set of functions wrapping K8S API calls.
'''

from django.conf import settings
from kubernetes import client
from kubeportal.k8s.utils import load_config, is_minikube
from base64 import b64decode

import logging

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


core_v1, rbac_v1 = load_config()


def create_k8s_ns(name):
    logger.info(
        "Creating Kubernetes namespace '{0}'".format(name))
    try:
        k8s_ns = client.V1Namespace(
            api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespace(k8s_ns)
    except client.rest.ApiException as e:
        # Race condition or earlier sync error - the K8S namespace is already there
        if e.status == 409:
            logger.warning("Tried to create already existing Kubernetes namespace {}. "
                           "Skipping the creation and using the existing one.".format(name))
        else:
            raise e
    return core_v1.read_namespace(name=name)


def delete_k8s_ns(name):
    if is_minikube():
        logger.info("Deleting Kubernetes namespace '{0}'".format(name))
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
        logger.exception("Error while fetching list of all pods from Kubernetes")
        return None


def get_pods_user(namespace):
    '''
    Get all pods for a specific Kubernetes namespace in the cluster.
    '''
    try:
        pods = core_v1.list_namespaced_pod(namespace)
        # logger.debug(f"Got list of pods for namespace {namespace}: {pods.items}")
        stripped_pods = []
        for pod in pods.items:
            stripped_pod = {'name': pod.metadata.name,
                            'creation_timestamp': pod.metadata.creation_timestamp}
            stripped_containers = []
            for container in pod.spec.containers:
                c = {'image': container.image,
                     'name': container.name}
                stripped_containers.append(c)
            stripped_pod['containers'] = stripped_containers
            stripped_pods.append(stripped_pod)
        return stripped_pods
    except Exception as e:
        logger.exception(f"Error while fetching pods of namespace {namespace}")
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
            if 'kube-proxy' in container.image:
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



