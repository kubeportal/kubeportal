'''
    A set of functions wrapping K8S API calls.
'''

from django.conf import settings
from kubernetes import client, config
from base64 import b64decode

import logging

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public']

try:
    # Production mode
    config.load_incluster_config()
except Exception:
    # Dev mode
    config.load_kube_config()

api_client = client.ApiClient()
core_v1 = client.CoreV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()
apps_v1 = client.AppsV1Api()
net_v1 = client.NetworkingV1beta1Api()

def is_minikube():
    '''
    Checks if the current context is minikube. This is needed for checks in the test code.
    '''
    contexts, active_context = config.list_kube_config_contexts()
    return active_context['context']['cluster'] == 'minikube'

def create_k8s_ns(name):
    '''
    Create the Kubernetes namespace with the given name in the cluster.
    An existing namespace with the same name leads to a no-op.
    '''
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


def create_k8s_deployment(namespace, name, replicas, match_labels, tpl):
    """
    Create a Kubernetes deployment in the cluster.
    """
    logger.info(f"Creating Kubernetes deployment '{name}'")
    k8s_containers = [client.V1Container(name=c["name"], image=c["image"]) for c in tpl["containers"]]
    k8s_pod_tpl = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(name=tpl['name'], labels=tpl['labels']),
        spec=client.V1PodSpec(containers=k8s_containers)
    )
    k8s_deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1DeploymentSpec(replicas=replicas,
                                     selector=client.V1LabelSelector(match_labels=match_labels),
                                     template=k8s_pod_tpl
                                     )
    )
    apps_v1.create_namespaced_deployment(namespace, k8s_deployment)


def delete_k8s_ns(name):
    '''
    Delete the given namespace in the cluster, but only when its Minikube.
    '''
    if is_minikube():
        logger.info("Deleting Kubernetes namespace '{0}'".format(name))
        core_v1.delete_namespace(name)
    else:
        logger.error("K8S namespace deletion not allowed in production clusters")


def get_namespaces():
    '''
    Returns the list of cluster namespaces, or None on error.
    '''
    try:
        return core_v1.list_namespace().items
    except Exception:
        logger.exception("Error while fetching namespaces from Kubernetes")
        return None

def get_ingress_hosts():
    '''
    Returns the list of host names used in ingresses accross all namespaces, 
    or None on error.
    '''
    try:
        ings =  net_v1.list_ingress_for_all_namespaces()
        host_list = [rule.host for ing in ings.items for rule in ing.spec.rules]
        return host_list

    except Exception:
        logger.exception("Error while fetching all ingresses from Kubernetes")
        return None


def get_service_accounts():
    '''
    Returns the list of service accounts in the cluster, or None on error.
    '''
    try:
        return core_v1.list_service_account_for_all_namespaces().items
    except Exception:
        logger.exception("Error while fetching service accounts from Kubernetes")
        return None


def get_pods():
    '''
    Returns the list of pods in the cluster, or None on error.
    '''
    try:
        return core_v1.list_pod_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all pods from Kubernetes")
        return None


def get_namespaced_pods(namespace):
    '''
    Get all pods for a specific Kubernetes namespace in the cluster.

    Make sure to update the 'Pod' component at static/docs/openapi_manual.yaml
    when touching this code.
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
        return []

def get_namespaced_deployments(namespace):
    '''
    Get all deployments for a specific Kubernetes namespace in the cluster.

    Make sure to update the 'Deployment' component at static/docs/openapi_manual.yaml
    when touching this code.
    '''
    try:
        deployments = apps_v1.list_namespaced_deployment(namespace)
        stripped_deployments = []
        for deployment in deployments.items:
            stripped_depl = {'name': deployment.metadata.name,
                             'creation_timestamp': deployment.metadata.creation_timestamp,
                             'replicas': deployment.spec.replicas}
            stripped_deployments.append(stripped_depl)
        return stripped_deployments
    except Exception as e:
        logger.exception(f"Error while fetching deployments of namespace {namespace}")
        return []

def get_namespaced_services(namespace):
    '''
    Get all services for a specific Kubernetes namespace in the cluster.

    Make sure to update the 'Service' component at static/docs/openapi_manual.yaml
    when touching this code.
    '''
    try:
        services = core_v1.list_namespaced_service(namespace)
        stripped_services = []
        for svc in services.items:
            stripped_svc = {'name': svc.metadata.name,
                             'creation_timestamp': svc.metadata.creation_timestamp}
            stripped_services.append(stripped_svc)
        return stripped_services
    except Exception as e:
        logger.exception(f"Error while fetching services of namespace {namespace}")
        return []


def get_namespaced_ingresses(namespace):
    '''
    Get all ingress for a specific Kubernetes namespace in the cluster.

    Make sure to update the 'Ingress' component at static/docs/openapi_manual.yaml
    when touching this code.
    '''
    try:
        ings = net_v1.list_namespaced_ingress(namespace)
        stripped_ings = []
        for ing in ings.items:
            stripped_ing = {'name': ing.metadata.name,
                            'creation_timestamp': ing.metadata.creation_timestamp,
                            'hosts': [rule.host for rule in ing.spec.rules]}
            stripped_ings.append(stripped_ing)
        return stripped_ings
    except Exception as e:
        logger.exception(f"Error while fetching ingresses of namespace {namespace}")
        return []


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



