from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api

import logging
logger = logging.getLogger('KubePortal')


class PodSerializer(serializers.Serializer):
    name = serializers.CharField()
    uid = serializers.CharField()
    creation_timestamp = serializers.DateTimeField(read_only=True)
    containers = serializers.ListField(child=serializers.DictField())


    @classmethod
    def to_json(cls, pod):
        """
        Get our stripped JSON representation of pod details.
        """
        stripped_pod = {'name': pod.metadata.name,
                        'uid': pod.metadata.uid,
                        'creation_timestamp': pod.metadata.creation_timestamp}
        stripped_containers = []
        for container in pod.spec.containers:
            c = {'image': container.image,
                 'name': container.name}
            stripped_containers.append(c)
        stripped_pod['containers'] = stripped_containers
        return stripped_pod


class PodView(generics.RetrieveAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pod by its UID."
    )
    def get(self, request, version, uid):
        pod = api.get_pod(uid)
        if request.user.has_namespace(pod.metadata.namespace):
            return Response(PodSerializer.to_json(pod))
        else:
            logger.warning(f"User '{request.user}' has no access to the namespace '{pod.metadata.namespace}' of pod '{pod.metadata.uid}'. Access denied.")
            raise NotFound


class PodsView(generics.ListAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get list of all pods in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            pod_list = api.get_namespaced_pods(namespace)
            return Response([reverse(viewname='pod', kwargs={'uid': pod.metadata.uid}, request=request) for pod in pod_list])
        else:
            logger.warning(f"User '{request.user}' has no access to pods of the namespace '{namespace}'. Access denied.")
            raise NotFound
