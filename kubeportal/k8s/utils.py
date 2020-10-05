from django.contrib import messages
from kubernetes import client, config

import logging
logger = logging.getLogger('KubePortal')


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


def error_log(request, error, additional_info, message):
    '''
    this error log method can be configured in different ways:
    - set additional_info to None and only e object is printed
    - use additional_info as single object param and param + error is printed
    - user additional_info as tuple of two objects
    '''
    logger.error("Exception: {0}".format(error))
    if additional_info is None:
        messages.error(
            request, message.format(error))
    elif isinstance(additional_info, tuple):
        messages.error(
            request, message.format(additional_info[0], additional_info[1], error))
    else:
        messages.error(
            request, message.format(additional_info, error))

