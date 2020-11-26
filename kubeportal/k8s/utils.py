from django.contrib import messages
from kubernetes import client, config


def load_config():
    try:
        # Production mode
        config.load_incluster_config()
    except Exception:
        # Dev mode
        config.load_kube_config()
    return client.CoreV1Api(), client.RbacAuthorizationV1Api()


def is_minikube():
    '''
    Checks if the current context is minikube. This is needed for checks in the test code.
    '''
    contexts, active_context = config.list_kube_config_contexts()
    return active_context['context']['cluster'] == 'minikube'


