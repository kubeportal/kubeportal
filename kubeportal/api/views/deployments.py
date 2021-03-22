import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api
from .pods import ContainerSerializer

logger = logging.getLogger('KubePortal')


class LabelSerializer(serializers.Serializer):
    """
    The API serializer for a label definition.
    """
    key = serializers.CharField()
    value = serializers.CharField()


class PodTemplateSerializer(serializers.Serializer):
    """
    The API serializer for a pod template.
    """
    name = serializers.CharField()
    labels = serializers.ListField(child=LabelSerializer())
    containers = serializers.ListField(child=ContainerSerializer())

class DeploymentListSerializer(serializers.Serializer):
    deployment_urls = serializers.ListField(child=serializers.URLField(), read_only=True)

class DeploymentSerializer(serializers.Serializer):
    """
    The API serializer for a single deployment.
    """
    name = serializers.CharField()
    puid = serializers.CharField(read_only=True)
    creation_timestamp = serializers.DateTimeField(read_only=True)
    replicas = serializers.IntegerField()
    match_labels = serializers.ListField(write_only=True, child=LabelSerializer())
    pod_template = PodTemplateSerializer(write_only=True)
    pod_urls = serializers.ListField(read_only=True, child=serializers.URLField())
    namespace_url = serializers.URLField(read_only=True)


class DeploymentRetrievalView(generics.RetrieveAPIView):
    serializer_class = DeploymentSerializer

    @extend_schema(
        summary="Get deployment by its UID."
    )
    def get(self, request, version, puid):
        namespace, name = puid.split('_')
        deployment = api.get_namespaced_deployment(namespace, name)

        if not request.user.has_namespace(deployment.metadata.namespace):
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{deployment.metadata.namespace}' of deployment '{deployment.metadata.uid}'. Access denied.")
            raise NotFound

        pod_list = api.get_deployment_pods(deployment)
        instance = DeploymentSerializer({
            'name': deployment.metadata.name,
            'puid': deployment.metadata.namespace + '_' + deployment.metadata.name,
            'creation_timestamp': deployment.metadata.creation_timestamp,
            'replicas': deployment.spec.replicas,
            'pod_urls': [reverse(viewname='pod_retrieval', kwargs={'puid': pod.metadata.namespace + '_' + pod.metadata.name}, request=request) for pod in
                         pod_list],
            'namespace_url': reverse(viewname='namespace', kwargs={'namespace': deployment.metadata.namespace},
                                     request=request)
        })
        return Response(instance.data)


class DeploymentsView(generics.RetrieveAPIView, generics.CreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return DeploymentListSerializer
        if self.request.method == "POST":
            return DeploymentSerializer

    @extend_schema(
        summary="Get the list of deployments in a namespace.",
        request=None,
        responses=DeploymentListSerializer
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            deployments = api.get_namespaced_deployments(namespace)
            puids = [item.metadata.namespace + '_' + item.metadata.name for item in deployments]
            instance = DeploymentListSerializer({
                'deployment_urls': [reverse(viewname='deployment_retrieval', kwargs={'puid': puid}, request=request) for puid in puids]\
            })

            return Response(instance.data)
        else:
            raise NotFound

    @extend_schema(
        summary="Create a deployment in a namespace.",
        request=DeploymentSerializer,
        responses=None
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_deployment(namespace,
                                      request.data["name"],
                                      request.data["replicas"],
                                      request.data["match_labels"],
                                      request.data["pod_template"])
            return Response(status=201)
        else:
            raise NotFound

