from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api

import logging
logger = logging.getLogger('KubePortal')



class DeploymentSerializer(serializers.Serializer):
    name = serializers.CharField()
    creation_timestamp = serializers.DateTimeField(read_only=True)
    replicas = serializers.IntegerField()
    pods = serializers.ListField(child=serializers.URLField())


    @classmethod
    def to_json(cls, deployment, request):
        """
        Get our stripped JSON representation of deployment details.
        """
        pod_list = api.get_deployment_pods(deployment)
        stripped_depl = {'name': deployment.metadata.name,
                         'creation_timestamp': deployment.metadata.creation_timestamp,
                         'replicas': deployment.spec.replicas,
                         'pods': [reverse(viewname='pod', kwargs={'uid': pod.metadata.uid}, request=request) for pod in pod_list]}
        return stripped_depl                         


class DeploymentView(generics.RetrieveAPIView):
    serializer_class = DeploymentSerializer

    @extend_schema(
        summary="Get deployment by its UID."
    )
    def get(self, request, version, uid):
        deployment = api.get_deployment(uid)
        if request.user.has_namespace(deployment.metadata.namespace):
            return Response(DeploymentSerializer.to_json(deployment, request))
        else:
            logger.warning(f"User '{request.user}' has no access to the namespace '{deployment.metadata.namespace}' of deployment '{deployment.metadata.uid}'. Access denied.")
            raise NotFound


class DeploymentsView(generics.ListCreateAPIView):
    serializer_class = DeploymentSerializer

    @extend_schema(
        summary="Get deployments in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            deployments = api.get_namespaced_deployments(namespace)
            return Response([reverse(viewname='deployment', kwargs={'uid': deployment.metadata.uid}, request=request) for deployment in deployments])
        else:
            # https://lockmedown.com/when-should-you-return-404-instead-of-403-http-status-code/
            logger.warning(f"User '{request.user}' has no access to deployments of the namespace '{namespace}'. Access denied.")
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
