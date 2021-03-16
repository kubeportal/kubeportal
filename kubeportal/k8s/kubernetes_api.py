"""
    A set of functions wrapping K8S API calls.

    Read-only methods put exceptions into the log file and return empty results on problems.
"""
import enum

from django.conf import settings
from kubernetes import client, config
from base64 import b64decode

import logging

from kubernetes.client import V1ServiceSpec, V1Service, NetworkingV1beta1Ingress, NetworkingV1beta1IngressSpec, \
    NetworkingV1beta1IngressTLS, NetworkingV1beta1IngressRule, NetworkingV1beta1HTTPIngressPath, \
    NetworkingV1beta1IngressBackend, NetworkingV1beta1HTTPIngressRuleValue

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
    """
    Checks if the current context is minikube. This is needed for checks in the test code.
    """
    try:
        contexts, active_context = config.list_kube_config_contexts()
        return active_context['context']['cluster'] == 'minikube'
    except Exception:
        return False


def create_k8s_ns(name: str):
    """
    Create the Kubernetes namespace with the given name in the cluster.
    An existing namespace with the same name leads to a no-op.

    Returns the new namespace.
    """
    try:
        k8s_ns = client.V1Namespace(
            api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespace(k8s_ns)
        logger.info("Created Kubernetes namespace '{0}'".format(name))
    except client.rest.ApiException as e:
        # Race condition or earlier sync error - the K8S namespace is already there
        if e.status == 409:
            logger.warning("Tried to create already existing Kubernetes namespace {}. "
                           "Skipping the creation and using the existing one.".format(name))
        else:
            raise e
    return core_v1.read_namespace(name=name)


def create_k8s_svca(namespace: str, name: str):
    """
    Create a Kubernetes service account in a namespace in the cluster.
    An existing service account with this name in this namespace leads to a no-op.

    Returns the new service account.
    """
    try:
        k8s_svca = client.V1ServiceAccount(
            api_version="v1", kind="ServiceAccount", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespaced_service_account(namespace=namespace, body=k8s_svca)
        logger.info(f"Created Kubernetes service account '{namespace}:{name}'")
    except client.rest.ApiException as e:
        # Race condition or earlier sync error - the K8S namespace is already there
        if e.status == 409:
            logger.warning(
                f"Tried to create already existing Kubernetes service account '{namespace}:{name}'. Skipping the creation and using the existing one.")
        else:
            raise e
    return core_v1.read_namespaced_service_account(namespace=namespace, name=name)


def create_k8s_deployment(namespace: str, name: str, replicas: int, match_labels: dict, template: dict):
    """
    Create a Kubernetes deployment in the cluster.

    Returns the new deployment.
    """
    logger.info(f"Creating Kubernetes deployment '{name}'")
    k8s_containers = [client.V1Container(name=c["name"], image=c["image"]) for c in template["containers"]]
    k8s_labels = {item['key']: item['value'] for item in template['labels']}
    k8s_pod_template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(name=template['name'], labels=k8s_labels),
        spec=client.V1PodSpec(containers=k8s_containers)
    )
    k8s_match_labels = {item['key']: item['value'] for item in match_labels}
    k8s_deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1DeploymentSpec(replicas=replicas,
                                     selector=client.V1LabelSelector(match_labels=k8s_match_labels),
                                     template=k8s_pod_template
                                     )
    )
    apps_v1.create_namespaced_deployment(namespace, k8s_deployment)


def delete_k8s_ns(name):
    """
    Delete the given namespace in the cluster, but only when its Minikube.
    """
    if is_minikube():
        logger.info("Deleting Kubernetes namespace '{0}'".format(name))
        core_v1.delete_namespace(name)
    else:
        logger.error("K8S namespace deletion not allowed in production clusters")


def delete_k8s_svca(name, namespace):
    """
    Delete the given service account in the given namespace in the cluster, but only when its Minikube.
    """
    if is_minikube():
        logger.info(f"Deleting Kubernetes service account '{namespace}:{name}'")
        core_v1.delete_namespaced_service_account(name=name, namespace=namespace)
    else:
        logger.error("K8S service account deletion not allowed in production clusters")


def get_namespaces():
    """
    Returns the list of cluster namespaces, or None on error.
    """
    try:
        return core_v1.list_namespace().items
    except Exception:
        logger.exception("Error while fetching namespaces from Kubernetes")
        return None


def get_ingress_hosts():
    """
    Returns the list of host names used in ingresses accross all namespaces,
    or None on error.
    """
    try:
        ings = net_v1.list_ingress_for_all_namespaces()
        host_list = [rule.host for ing in ings.items for rule in ing.spec.rules]
        return host_list

    except Exception:
        logger.exception("Error while fetching all ingresses from Kubernetes")
        return None


def get_service_accounts():
    """
    Returns the list of service accounts in the cluster, or None on error.
    """
    try:
        return core_v1.list_service_account_for_all_namespaces().items
    except Exception:
        logger.exception("Error while fetching service accounts from Kubernetes")
        return None


def get_pods():
    """
    Returns the list of pods in the cluster, or None on error.
    """
    try:
        return core_v1.list_pod_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all pods from Kubernetes")
        return None


def get_pod(uid):
    """
    Get pod in the cluster by its uid.
    """
    try:
        pods = get_pods()
        for pod in pods:
            if pod.metadata.uid == uid:
                return pod
        return None
    except Exception as e:
        logger.exception(f"Error while fetching pod with uid {uid}")
        return None


def get_ingresses():
    """
    Returns the list of ingresses in the cluster, or None on error.
    """
    try:
        return net_v1.list_ingress_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all ingresses from Kubernetes")
        return None


def get_ingress(uid):
    """
    Get ingress in the cluster by its uid.
    """
    try:
        ingresses = get_ingresses()
        for ingress in ingresses:
            if ingress.metadata.uid == uid:
                return ingress
        return None
    except Exception as e:
        logger.exception(f"Error while fetching ingress with uid {uid}")
        return None


def get_namespaced_pods(namespace):
    """
    Get all pods for a specific Kubernetes namespace in the cluster.
    """
    try:
        return core_v1.list_namespaced_pod(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching pods of namespace {namespace}")
        return []


def get_namespaced_deployments(namespace):
    """
    Get all deployments for a specific Kubernetes namespace in the cluster.
    """
    try:
        return apps_v1.list_namespaced_deployment(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching deployments of namespace {namespace}")
        return None


def get_deployment_pods(deployment):
    """
    Gets a list of pod API objects belonging to a deployment API object.
    """
    ns = deployment.metadata.namespace
    selector = deployment.spec.selector  # V1LabelSelector
    selector_str = ",".join([k + '=' + v for k, v in selector.match_labels.items()])
    try:
        return core_v1.list_namespaced_pod(namespace=ns, label_selector=selector_str).items
    except Exception as e:
        logger.exception(f"Error while fetching pods of deployment {deployment.metadata.name}")
        return None


def get_deployments():
    """
    Returns the list of deployments in the cluster, or None on error.
    """
    try:
        return apps_v1.list_deployment_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all deployments from Kubernetes")
        return None


def get_deployment(uid):
    """
    Get deployment in the cluster by its uid.
    """
    try:
        deployments = get_deployments()
        for deployment in deployments:
            if deployment.metadata.uid == uid:
                return deployment
        return None
    except Exception as e:
        logger.exception(f"Error while fetching deployment with uid {uid}")
        return None


def get_services():
    """
    Returns the list of services in the cluster, or None on error.
    """
    try:
        return core_v1.list_service_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all deployments from Kubernetes")
        return None


def get_service(uid):
    """
    Get service in the cluster by its uid.
    """
    try:
        services = get_services()
        for service in services:
            if service.metadata.uid == uid:
                return service
        return None
    except Exception as e:
        logger.exception(f"Error while fetching service with uid {uid}")
        return None


def get_namespaced_services(namespace):
    """
    Get all services for a specific Kubernetes namespace in the cluster.
    """
    try:
        return core_v1.list_namespaced_service(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching services of namespace {namespace}")
        return None


def get_namespaced_services_json(namespace):
    """
    Get all services for a specific Kubernetes namespace in the cluster.
    """
    try:
        services = core_v1.list_namespaced_service(namespace)
        stripped_services = []
        for svc in services.items:
            if svc.spec.selector:
                selector = [{'key': k, 'value': v} for k, v in svc.spec.selector.items()]
            else:
                selector = None
            stripped_svc = {'name': svc.metadata.name,
                            'type': svc.spec.type,
                            'selector': selector,
                            'creation_timestamp': svc.metadata.creation_timestamp}
            ports = []
            for port in svc.spec.ports:
                ports.append({"port": port.port, "protocol": port.protocol})
            stripped_svc["ports"] = ports
            stripped_services.append(stripped_svc)
        return stripped_services
    except Exception as e:
        logger.exception(f"Error while fetching services of namespace {namespace}")
        return []


def create_k8s_service(namespace: str, name: str, svc_type: str, selector: list, ports: list):
    """
    Create a Kubernetes service in the cluster.
    The 'ports' parameter contains a list of dictionaries, each with the key 'port' and 'protocol'.
    """
    logger.info(f"Creating Kubernetes service '{name}'")
    svc_ports = [client.V1ServicePort(name=str(p["port"]), port=p["port"], protocol=p["protocol"]) for p in ports]

    svc = V1Service(
        metadata=client.V1ObjectMeta(name=name),
        spec=V1ServiceSpec(
            type=svc_type,
            selector={item['key']: item['value'] for item in selector},
            ports=svc_ports
        )
    )
    core_v1.create_namespaced_service(namespace, svc)


def create_k8s_ingress(namespace: str, name: str, annotations: dict, tls: bool, rules: dict):
    """
    Create a Kubernetes ingress in the cluster.

    The Kubeportal API makes some simplifying assumptions:

    - TLS is a global configuration for an Ingress.
    - The necessary annotations come from the portal settings, not from the ingress definition.
    """
    logger.info(f"Creating Kubernetes ingress '{name}'")

    k8s_annotations = {item['key']: item['value'] for item in annotations}

    k8s_ing = NetworkingV1beta1Ingress(
        metadata=client.V1ObjectMeta(name=name, annotations=k8s_annotations)
    )

    k8s_rules = []
    k8s_hosts = []
    for rule in rules:
        host = rule["host"]
        k8s_hosts.append(host)
        paths = rule["paths"]
        k8s_rule = NetworkingV1beta1IngressRule(host=host)
        k8s_paths = []
        for path_config in paths:
            k8s_backend = NetworkingV1beta1IngressBackend(
                service_name=path_config['service_name'],
                service_port=path_config['service_port']
            )
            k8s_paths.append(NetworkingV1beta1HTTPIngressPath(path=path_config["path"], backend=k8s_backend))
        k8s_http = NetworkingV1beta1HTTPIngressRuleValue(
            paths=k8s_paths
        )
        k8s_rule.http = k8s_http
        k8s_rules.append(k8s_rule)

    k8s_spec = NetworkingV1beta1IngressSpec(rules=k8s_rules)

    if tls:
        k8s_ing.metadata.annotations['cert-manager.io/cluster-issuer'] = settings.INGRESS_TLS_ISSUER
        k8s_spec.tls = [NetworkingV1beta1IngressTLS(hosts=k8s_hosts, secret_name=f'{name}_tls')]

    k8s_ing.spec = k8s_spec
    net_v1.create_namespaced_ingress(namespace, k8s_ing)


def get_namespaced_ingresses(namespace):
    """
    Get all ingresses for a specific Kubernetes namespace in the cluster.
    """
    try:
        return net_v1.list_namespaced_ingress(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching ingresses of namespace {namespace}")
        return None


def get_namespaced_ingresses_json(namespace):
    """
    Get all ingress for a specific Kubernetes namespace in the cluster.
    Error handling is supposed to happen on the caller side.
    """
    ings = net_v1.list_namespaced_ingress(namespace)
    stripped_ings = []
    for ing in ings.items:
        stripped_ing = {'name': ing.metadata.name,
                        'creation_timestamp': ing.metadata.creation_timestamp,
                        'annotations': ing.metadata.annotations,
                        }
        if ing.spec.tls:
            stripped_ing['tls'] = True
        else:
            stripped_ing['tls'] = False
        rules = {}
        for rule in ing.spec.rules:
            rules[rule.host] = {}
            for path_setting in rule.http.paths:
                rules[rule.host][path_setting.path] = {}
                rules[rule.host][path_setting.path]['service_name'] = path_setting.backend.service_name
                rules[rule.host][path_setting.path]['service_port'] = path_setting.backend.service_port
        stripped_ing['rules'] = rules
        stripped_ings.append(stripped_ing)
    return stripped_ings


def get_token(kubeportal_service_account):
    """
    Returns the secret K8S login token as base64-encoded string.
    """
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


def check_role_bindings(ns):
    """
    Check, and fix in case, the role bindings for this namespace in the cluster. The list of expected
    cluster roles to be bound to comes from the application settings.

    We only consider visible namespaces here, to prevent hitting special namespaces and giving them
    (most likely unnecessary) additional role bindings
    """
    if not ns.visible:
        logger.debug(f"Namespace '{ns.name}' is invisible, skipping role binding check.")
        return

    try:
        rolebindings = rbac_v1.list_namespaced_role_binding(ns.name).items
    except Exception as e:
        logger.exception(f"Could not fetch role bindings for namespace {self}")
        return False

    # Get all cluster roles this namespace is currently bound to
    clusterroles_active = [rolebinding.role_ref.name for rolebinding in rolebindings if
                           rolebinding.role_ref.kind == 'ClusterRole']
    logger.debug(f"Namespace '{ns.name}' is currently bound to cluster roles {clusterroles_active}")

    # Check list of default cluster roles from settings
    for clusterrole in settings.NAMESPACE_CLUSTERROLES:
        if clusterrole not in clusterroles_active:
            logger.info(f"Namespace '{ns.name}' is not bound to cluster role '{clusterrole}', fixing this ...")
            create_role_binding(ns, clusterrole)

    return True


def create_role_binding(ns, clusterrole):
    """
    Create a role binding to the given cluster role for the given namespace in the cluster.
    """
    try:
        role_ref = client.V1RoleRef(name=clusterrole, kind="ClusterRole", api_group="rbac.authorization.k8s.io")

        # Subject for the cluster role are all service accounts in the namespace
        subject = client.V1Subject(name="system:serviceaccounts:" + ns.name, kind="Group",
                                   api_group="rbac.authorization.k8s.io")
        metadata = client.V1ObjectMeta(name=clusterrole)
        new_rolebinding = client.V1RoleBinding(role_ref=role_ref, metadata=metadata, subjects=[subject, ])

        rbac_v1.create_namespaced_role_binding(ns.name, new_rolebinding)
    except Exception as e:
        logger.exception(f"Could not create role binding of namespace '{self.name}' to '{clusterrole}'")
