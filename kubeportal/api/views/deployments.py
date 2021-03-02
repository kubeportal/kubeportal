from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api


class DeploymentView(generics.RetrieveAPIView):
    pass

class DeploymentsView(generics.ListCreateAPIView):
    @extend_schema(
        summary="Get deployments in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            deployments = api.get_namespaced_deployments(namespace)
            stripped_deployments = []
            for deployment in deployments:
                pod_list = api.get_deployment_pods(deployment)
                stripped_depl = {'name': deployment.metadata.name,
                                 'creation_timestamp': deployment.metadata.creation_timestamp,
                                 'replicas': deployment.spec.replicas,
                                 'pods': [reverse(viewname='pod', kwargs={'uid': pod.metadata.uid}, request=request) for pod in pod_list]
                                 }
                stripped_deployments.append(stripped_depl)
            return Response(stripped_deployments)
        else:
            # https://lockmedown.com/when-should-you-return-404-instead-of-403-http-status-code/
            raise NotFound

    @extend_schema(
        summary="Create a deployment in a namespace."
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_deployment(namespace,
                                      request.data["name"],
                                      request.data["replicas"],
                                      request.data["matchLabels"],
                                      request.data["template"])
            return Response(status=201)
        else:
            raise NotFound
