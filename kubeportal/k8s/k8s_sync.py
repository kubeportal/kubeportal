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

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount

logger = logging.getLogger('KubePortal')

def sync(request=None):
    '''
    Synchronizes the local shallow copy of Kubernetes data.
    Returns True on success.
    '''
    try:
        res1 = KubernetesNamespace.create_missing_in_portal()
        res2 = KubernetesNamespace.create_missing_in_cluster()
        res3 = KubernetesServiceAccount.create_missing_in_portal()
        res4 = KubernetesServiceAccount.create_missing_in_cluster()
        if request:
            messages.info(request, "Synchronization finished.")
        logger.debug("Synchronization finished.")
        return True == res1 == res2 == res3 == res4
    except client.rest.ApiException as e:
        msg = json.loads(e.body)['message']
        logger.error(
            "API server exception during synchronization: {0}".format(msg))
        if request:
            messages.error(
                request, "Kubernetes returned an error during synchronization: {0}".format(msg))
        return False
