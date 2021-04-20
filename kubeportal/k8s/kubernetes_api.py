"""
    A set of functions wrapping K8S API calls.
    Read-only methods put exceptions into the log file and return empty results on problems.
"""

from django.conf import settings
from kubernetes import client, config
from base64 import b64decode

import logging

logger = logging.getLogger('KubePortal')

HIDDEN_NAMESPACES = ['kube-system', 'kube-public']


### Helper functions for accessing the Kubernetes API server with
### permissions of the running portal software

def get_portal_configuration():
    """
    Get a configuration for the Kubernetes client library.
    The credentials of the running Kubeportal software are used. 

    Returns None on error. 
    """
    try:
        # Kubeportal runs as pod in Kubernetes
        return config.load_incluster_config()
    except Exception:
        try:
            # There is a ~/.kube/config file available
            # This is the typical mode on developer machines,
            # or when Kubeportal runs as Docker container outside of K8S
            return config.load_kube_config()
        except Exception:
            # We have no user token to use, and all helpers failed
            logger.error("Could not load Kubernetes configuration with helpers.")
            return None


def get_portal_api_client():
    configuration = get_portal_configuration()
    return client.ApiClient(configuration)


def get_portal_core_v1():
    api_client = get_portal_api_client()
    return client.CoreV1Api(api_client)


def get_portal_rbac_v1():
    api_client = get_portal_api_client()
    return client.RbacAuthorizationV1Api(api_client)


def get_portal_apps_v1():
    api_client = get_portal_api_client()
    return client.AppsV1Api(api_client)


def get_portal_net_v1():
    api_client = get_portal_api_client()
    return client.NetworkingV1beta1Api(api_client)


### Helper functions for accessing the Kubernetes API server with
### permissions of a given single user

def get_token(kubeportal_service_account):
    """
    Returns the secret K8S login token for a portal user as base64-encoded string.
    """
    core_v1 = get_portal_core_v1()
    service_account = core_v1.read_namespaced_service_account(
        name=kubeportal_service_account.name,
        namespace=kubeportal_service_account.namespace.name)
    secret_name = service_account.secrets[0].name
    secret = core_v1.read_namespaced_secret(
        name=secret_name, namespace=kubeportal_service_account.namespace.name)
    encoded_token = secret.data['token']
    return b64decode(encoded_token).decode()


def get_user_configuration(user):
    """
    Get a configuration for the Kubernetes client library.
    The credentials of the given portal user are used. 

    Returns None on error. 
    """
    if not user.has_access_approved():
        logger.error("Kubernetes API configuration for user unavailable, user is not approved.")
        return None
    configuration = client.Configuration()
    configuration.api_key['authorization'] = get_token(user.service_account)
    if not settings.API_SERVER_EXTERNAL:
        logger.error("Kubernetes API configuration for user unavailable, API_SERVER_EXTERNAL is not set.")
        return None
    configuration.host = settings.API_SERVER_EXTERNAL
    return configuration


def get_user_api_client(user):
    configuration = get_user_configuration(user)
    return client.ApiClient(configuration)


def get_user_core_v1(user):
    api_client = get_user_api_client(user)
    return client.CoreV1Api(api_client)


def get_user_rbac_v1(user):
    api_client = get_user_api_client(user)
    return client.RbacAuthorizationV1Api(api_client)


def get_user_apps_v1(user):
    api_client = get_user_api_client(user)
    return client.AppsV1Api(api_client)


def get_user_net_v1(user):
    api_client = get_user_api_client(user)
    return client.NetworkingV1beta1Api(api_client)

# General functions

def is_minikube():
    """
    Checks if the current context is minikube. This is needed for checks in the test code.
    """
    try:
        contexts, active_context = config.list_kube_config_contexts()
        return active_context['context']['cluster'] == 'minikube'
    except Exception:
        return False

# Namespaces

def create_k8s_ns(name: str):
    """
    Create the Kubernetes namespace with the given name in the cluster.
    An existing namespace with the same name leads to a no-op.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.

    Returns the new namespace object.
    """
    core_v1 = get_portal_core_v1()
    try:
        k8s_ns = client.V1Namespace(
            api_version="v1", kind="Namespace", metadata=client.V1ObjectMeta(name=name))
        core_v1.create_namespace(k8s_ns)
        logger.info("Created Kubernetes namespace '{0}'".format(name))
    except client.rest.ApiException as e:
        # Race condition or earlier sync error - the K8S namespace is already there
        if e.status == 409:
            logger.warning(
                f"Tried to create already existing Kubernetes namespace {name}. Skipping the creation and using the existing one.")
        else:
            raise e
    return core_v1.read_namespace(name=name)


def delete_k8s_ns(name):
    """
    Delete the given namespace in the cluster, but only when its Minikube.
    """
    if is_minikube():
        logger.info("Deleting Kubernetes namespace '{0}'".format(name))
        core_v1 = get_portal_core_v1()
        core_v1.delete_namespace(name)
    else:
        logger.error("K8S namespace deletion not allowed in production clusters.")


def get_namespaces():
    """
    Returns the list of cluster namespaces, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    core_v1 = get_portal_core_v1()
    try:
        return core_v1.list_namespace().items
    except Exception:
        logger.exception("Error while fetching namespaces from Kubernetes")
        return None

# Service Accounts

def create_k8s_svca(namespace: str, name: str):
    """
    Create a Kubernetes service account in a namespace in the cluster.
    An existing service account with this name in this namespace leads to a no-op.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.

    Returns the new service account.
    """
    core_v1 = get_portal_core_v1()
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


def delete_k8s_svca(name, namespace):
    """
    Delete the given service account in the given namespace in the cluster, but only when its Minikube.
    """
    if is_minikube():
        core_v1 = get_portal_core_v1()
        logger.info(f"Deleting Kubernetes service account '{namespace}:{name}'")
        core_v1.delete_namespaced_service_account(name=name, namespace=namespace)
    else:
        logger.error("K8S service account deletion not allowed in production clusters")


def get_service_accounts():
    """
    Returns the list of service accounts in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    core_v1 = get_portal_core_v1()
    try:
        return core_v1.list_service_account_for_all_namespaces().items
    except Exception:
        logger.exception("Error while fetching service accounts from Kubernetes")
        return None


### Persistent Volume Claims

def create_k8s_pvc(namespace: str, name: str, access_modes: tuple, storage_class_name: str, size: str, user):
    """
    Create a Kubernetes persistent volume claim in a namespace in the cluster.
    An existing pvc with this name in this namespace leads to a no-op.

    Returns the new pvc.
    """
    core_v1 = get_user_core_v1(user)
    try:
        k8s_spec = client.V1PersistentVolumeClaimSpec(
            access_modes=access_modes,
            storage_class_name=storage_class_name,
            resources=client.V1ResourceRequirements(requests={'storage': size})
        )
        k8s_pvc = client.V1PersistentVolumeClaim(
            api_version="v1",
            kind="PersistentVolumeClaim",
            metadata=client.V1ObjectMeta(name=name),
            spec=k8s_spec)
        core_v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=k8s_pvc)
        logger.info(f"Created Kubernetes pvc '{namespace}:{name}'")
    except client.rest.ApiException as e:
        if e.status == 409:
            logger.warning(
                f"Tried to create already existing Kubernetes pvc '{namespace}:{name}'. Skipping the creation and using the existing one.")
        else:
            raise e
    return core_v1.read_namespaced_persistent_volume_claim(namespace=namespace, name=name)


def delete_k8s_pvc(name: str, namespace: str, user):
    """
    Delete the given pvc in the given namespace in the cluster, but only when its Minikube.
    """
    if is_minikube():
        core_v1 = get_user_core_v1(user)
        logger.info(f"Deleting Kubernetes pvc '{namespace}:{name}'")
        core_v1.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace)
    else:
        logger.error("K8S pvc deletion not allowed in production clusters")


def get_namespaced_pvcs(namespace: str, user):
    """
    Get all pvcs for a specific Kubernetes namespace in the cluster.
    """
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.list_namespaced_persistent_volume_claim(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching persistent volume claims of namespace {namespace}")
        return None


def get_pvcs():
    """
    Returns the list of pvcs in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    core_v1 = get_portal_core_v1()
    try:
        return core_v1.list_persistent_volume_claim_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all pvcs from Kubernetes")
        return None


def get_namespaced_pvc(namespace: str, name: str, user):
    """
    Get pvc in the cluster in a particular namespace.
    """
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.read_namespaced_persistent_volume_claim(name, namespace)
    except Exception as e:
        logger.exception(f"Error while fetching persistent volume claim.")
        return None


### Deployments

def create_k8s_deployment(namespace: str, name: str, replicas: int, match_labels: dict, template: dict, user):
    """
    Create a Kubernetes deployment in the cluster.

    Returns the new deployment.
    """
    apps_v1 = get_user_apps_v1(user)
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


def get_namespaced_deployments(namespace, user):
    """
    Get all deployments for a specific Kubernetes namespace in the cluster.
    """
    apps_v1 = get_user_apps_v1(user)
    try:
        return apps_v1.list_namespaced_deployment(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching deployments of namespace {namespace}")
        return None


def get_deployments():
    """
    Returns the list of deployments in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    apps_v1 = get_portal_apps_v1()
    try:
        return apps_v1.list_deployment_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all deployments from Kubernetes")
        return None


def get_namespaced_deployment(namespace: str, name: str, user):
    """
    Get deployment in the cluster by its namespace and name.
    """
    apps_v1 = get_user_apps_v1(user)
    try:
        return apps_v1.read_namespaced_deployment(name, namespace)
    except Exception as e:
        logger.exception(f"Error while fetching deployment.")
        return None


### Pods

def create_k8s_pod(namespace: str, name: str, containers: int, user):
    """
    Create a Kubernetes pod in the cluster.

    Returns a status code to be used as result:

    201 - successfully created
    409 - pod with this name already exists
    """
    core_v1 = get_user_core_v1(user)
    logger.info(f"Creating Kubernetes pod '{name}'")
    k8s_containers = [client.V1Container(name=c["name"], image=c["image"]) for c in containers]
    k8s_pod = client.V1Pod(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1PodSpec(containers=k8s_containers)
    )
    try:
        core_v1.create_namespaced_pod(namespace, k8s_pod)
        return 201
    except client.ApiException as e:
        return e.status


def get_pods():
    """
    Returns the list of pods in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    core_v1 = get_portal_core_v1()
    try:
        return core_v1.list_pod_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all pods from Kubernetes")
        return None


def get_namespaced_pod(namespace: str, name: str, user):
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.read_namespaced_pod(name, namespace)
    except Exception as e:
        logger.exception(f"Error while fetching pod {namespace}:{name}")
        return None


def get_namespaced_pods(namespace: str, user):
    """
    Get all pods for a specific Kubernetes namespace in the cluster.
    """
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.list_namespaced_pod(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching pods of namespace {namespace}")
        return []


def get_deployment_pods(deployment, user):
    """
    Gets a list of pod API objects belonging to a deployment API object.
    """
    core_v1 = get_user_core_v1(user)
    ns = deployment.metadata.namespace
    selector = deployment.spec.selector  # V1LabelSelector
    selector_str = ",".join([k + '=' + v for k, v in selector.match_labels.items()])
    try:
        return core_v1.list_namespaced_pod(namespace=ns, label_selector=selector_str).items
    except Exception as e:
        logger.exception(f"Error while fetching pods of deployment {deployment.metadata.name}")
        return None


### Ingresses

def get_ingress_hosts():
    """
    Returns the list of host names used in ingresses accross all namespaces,
    or None on error.
    """
    net_v1 = get_portal_net_v1()
    try:
        ings = net_v1.list_ingress_for_all_namespaces()
        host_list = [rule.host for ing in ings.items for rule in ing.spec.rules]
        return host_list

    except Exception:
        logger.exception("Error while fetching all ingresses from Kubernetes")
        return None


def get_ingresses():
    """
    Returns the list of ingresses in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    net_v1 = get_portal_net_v1()
    try:
        return net_v1.list_ingress_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all ingresses from Kubernetes")
        return None


def get_namespaced_ingress(namespace: str, name: str, user):
    """
    Get ingress in the cluster.
    """
    net_v1 = get_user_net_v1(user)
    return net_v1.read_namespaced_ingress(name, namespace)


def get_namespaced_ingresses(namespace: str, user):
    """
    Get all ingresses for a specific Kubernetes namespace in the cluster.
    """
    net_v1 = get_user_net_v1(user)
    try:
        return net_v1.list_namespaced_ingress(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching ingresses of namespace {namespace}")
        return None


def get_namespaced_ingresses_json(namespace: str, user):
    """
    Get all ingress for a specific Kubernetes namespace in the cluster.
    Error handling is supposed to happen on the caller side.
    """
    net_v1 = get_user_net_v1(user)
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


def create_k8s_ingress(namespace: str, name: str, annotations: dict, tls: bool, rules: dict, user):
    """
    Create a Kubernetes ingress in the cluster.

    The Kubeportal API makes some simplifying assumptions:

    - TLS is a global configuration for an Ingress.
    - The necessary annotations come from the portal settings, not from the ingress definition.
    """
    net_v1 = get_user_net_v1(user)
    logger.info(f"Creating Kubernetes ingress '{name}'")

    k8s_annotations = {item['key']: item['value'] for item in annotations}

    k8s_ing = client.NetworkingV1beta1Ingress(
        metadata=client.V1ObjectMeta(name=name, annotations=k8s_annotations)
    )

    k8s_rules = []
    k8s_hosts = []
    for rule in rules:
        host = rule["host"]
        k8s_hosts.append(host)
        paths = rule["paths"]
        k8s_rule = client.NetworkingV1beta1IngressRule(host=host)
        k8s_paths = []
        for path_config in paths:
            k8s_backend = client.NetworkingV1beta1IngressBackend(
                service_name=path_config['service_name'],
                service_port=path_config['service_port']
            )
            k8s_paths.append(
                client.NetworkingV1beta1HTTPIngressPath(path=path_config.get("path", None), backend=k8s_backend))
        k8s_http = client.NetworkingV1beta1HTTPIngressRuleValue(
            paths=k8s_paths
        )
        k8s_rule.http = k8s_http
        k8s_rules.append(k8s_rule)

    k8s_spec = client.NetworkingV1beta1IngressSpec(rules=k8s_rules)

    if tls:
        k8s_ing.metadata.annotations['cert-manager.io/cluster-issuer'] = settings.INGRESS_TLS_ISSUER
        k8s_spec.tls = [client.NetworkingV1beta1IngressTLS(hosts=k8s_hosts, secret_name=f'{name}_tls')]

    k8s_ing.spec = k8s_spec
    net_v1.create_namespaced_ingress(namespace, k8s_ing)


### Services

def get_services():
    """
    Returns the list of services in the cluster, or None on error.

    This operation is performed by portal backend admins, which may not have
    enough permissions. It is also non-destructive, so we run it with portal permissions.
    """
    core_v1 = get_portal_core_v1()
    try:
        return core_v1.list_service_for_all_namespaces().items
    except Exception as e:
        logger.exception("Error while fetching list of all deployments from Kubernetes")
        return None


def get_namespaced_service(namespace: str, name: str, user):
    """
    Get service in the cluster.
    """
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.read_namespaced_service(name, namespace)
    except Exception as e:
        logger.exception(f"Error while fetching service.")
        return None


def get_namespaced_services(namespace: str, user):
    """
    Get all services for a specific Kubernetes namespace in the cluster.
    """
    core_v1 = get_user_core_v1(user)
    try:
        return core_v1.list_namespaced_service(namespace).items
    except Exception as e:
        logger.exception(f"Error while fetching services of namespace {namespace}")
        return None


def get_namespaced_services_json(namespace: str, user):
    """
    Get all services for a specific Kubernetes namespace in the cluster.
    """
    core_v1 = get_user_core_v1(user)
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


def create_k8s_service(namespace: str, name: str, svc_type: str, selector: list, ports: list, user):
    """
    Create a Kubernetes service in the cluster.
    The 'ports' parameter contains a list of dictionaries, each with the key 'port' and 'protocol'.
    """
    core_v1 = get_user_core_v1(user)
    logger.info(f"Creating Kubernetes service '{name}'")
    svc_ports = [client.V1ServicePort(name=str(p["port"]), port=p["port"], protocol=p["protocol"]) for p in ports]

    svc = client.V1Service(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1ServiceSpec(
            type=svc_type,
            selector={item['key']: item['value'] for item in selector},
            ports=svc_ports
        )
    )
    core_v1.create_namespaced_service(namespace, svc)


### Statistics

def get_apiserver():
    if settings.API_SERVER_EXTERNAL:
        return settings.API_SERVER_EXTERNAL
    else:
        core_v1 = get_portal_core_v1()
        return core_v1.api_client.configuration.host


def get_kubernetes_version():
    core_v1 = get_portal_core_v1()
    pods = core_v1.list_namespaced_pod("kube-system").items
    for pod in pods:
        for container in pod.spec.containers:
            if 'kube-proxy' in container.image:
                return container.image.split(":")[1]
    logger.error(f"Kubernetes version not identifiable, list of pods in 'kube-system': {pods}.")
    return None


def get_number_of_pods():
    core_v1 = get_portal_core_v1()
    return len(core_v1.list_pod_for_all_namespaces().items)


def get_number_of_nodes():
    core_v1 = get_portal_core_v1()
    return len(core_v1.list_node().items)


def get_number_of_cpus():
    core_v1 = get_portal_core_v1()
    nodes = core_v1.list_node().items
    return sum([int(node.status.capacity['cpu']) for node in nodes])


def get_memory_sum():
    core_v1 = get_portal_core_v1()
    nodes = core_v1.list_node().items
    mems = [int(node.status.capacity['memory'][:-2]) for node in nodes]
    return sum(mems) / 1000000  # in GiBytes


def get_number_of_volumes():
    core_v1 = get_portal_core_v1()
    return len(core_v1.list_persistent_volume().items)
