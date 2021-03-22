from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api

import logging

logger = logging.getLogger('KubePortal')


class ContainerSerializer(serializers.Serializer):
    """
    The API serializer for a container.
    """
    name = serializers.CharField()
    image = serializers.CharField()


class PodSerializer(serializers.Serializer):
    """
    The API serializer for a pod.
    """
    name = serializers.CharField()
    puid = serializers.CharField(read_only=True)
    creation_timestamp = serializers.DateTimeField(read_only=True)
    containers = serializers.ListField(child=ContainerSerializer())


class PodListSerializer(serializers.Serializer):
    pod_urls = serializers.ListField(read_only=True, child=serializers.URLField())

class PodRetrievalView(generics.RetrieveAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pod by its PUID."
    )
    def get(self, request, version, puid):
        namespace, pod_name = puid.split('_')
        pod = api.get_namespaced_pod(namespace, pod_name)
        if not pod:
            logger.error(f"Pod {pod_name} in namespace {namespace} not found.")
            raise NotFound
        if request.user.has_namespace(namespace):
            container_instances = []
            for container in pod.spec.containers:
                instance = ContainerSerializer({
                    'image': container.image,
                    'name': container.name})
                container_instances.append(instance.data)

            pod_instance = PodSerializer({
                'name': pod.metadata.name,
                'puid': pod.metadata.namespace + "_" + pod.metadata.name,
                'creation_timestamp': pod.metadata.creation_timestamp,
                'containers': container_instances})

            return Response(pod_instance.data)
        else:
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{pod.metadata.namespace}' of pod '{pod.metadata.uid}'. Access denied.")
            raise NotFound

class PodsView(generics.RetrieveAPIView, generics.CreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return PodListSerializer
        if self.request.method == "POST":
            return PodSerializer

    @extend_schema(
        summary="Get the list of pods in a namespace.",
        request=None,
        responses=PodListSerializer
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            pods = api.get_namespaced_pods(namespace)
            puids = [item.metadata.namespace + "_" + item.metadata.name for item in pods]

            instance = PodListSerializer({
                'pod_urls': [reverse(viewname='pod_retrieval', kwargs={'puid': puid}, request=request) for puid in puids]\
            })
            return Response(instance.data)
        else:
            raise NotFound

    @extend_schema(
        summary="Create a deployment in a namespace.",
        request=PodSerializer,
        responses=None
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(status=api.create_k8s_pod(  namespace,
                                                        request.data["name"],
                                                        request.data["containers"]))
        else:
            raise NotFound



