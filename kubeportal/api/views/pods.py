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

    @classmethod
    def to_json(cls, pod):
        """
        Get our stripped JSON representation of pod details.
        """
        stripped_pod = {'name': pod.metadata.name,
                        'puid': pod.metadata.namespace + "_" + pod.metadata.name,
                        'creation_timestamp': pod.metadata.creation_timestamp}
        stripped_containers = []
        for container in pod.spec.containers:
            c = {'image': container.image,
                 'name': container.name}
            stripped_containers.append(c)
        stripped_pod['containers'] = stripped_containers
        return stripped_pod

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
            return Response(PodSerializer.to_json(pod))
        else:
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{pod.metadata.namespace}' of pod '{pod.metadata.uid}'. Access denied.")
            raise NotFound

class PodsView(generics.RetrieveAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return PodListSerializer

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




