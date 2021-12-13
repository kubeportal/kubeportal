from django.conf import settings
from django.http import request, response
from django.http.response import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotAcceptable, NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse
from kubeportal.elastic.elastic_client import ElasticSearchClient
from wsgiref.util import FileWrapper



from kubeportal.k8s import kubernetes_api as api

import logging

logger = logging.getLogger('KubePortal')


class VolumeSerializer(serializers.Serializer):
    """
    The API serializer for a volume.
    """
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    path = serializers.CharField(read_only=True)


class VolumeMountSerializer(serializers.Serializer):
    """
    The API serializer for a container volume mount.
    """
    volume = VolumeSerializer(read_only=True)
    mount_path = serializers.CharField(read_only=True)


class ContainerSerializer(serializers.Serializer):
    """
    The API serializer for a container.
    """
    name = serializers.CharField()
    image = serializers.CharField()
    volume_mounts = serializers.ListField(read_only=True, child=VolumeMountSerializer())

    @classmethod
    def create_from_k8s_container(cls, k8s_container, k8s_pod):
        # step through pod volumes and get serialized information
        volume_list = {}
        for k8s_volume in k8s_pod.spec.volumes:
            k8s_volume_data = k8s_volume.to_dict()
            # see V1Volume definition for the idea here
            volume_type = ""
            for k, v in k8s_volume_data.items():
                if v is not None and k not in ['name',]:
                    volume_type = k
            volume_name = k8s_volume.name
            volume_path = ""
            # Type-specific considerations
            if volume_type == 'host_path':
                volume_path = k8s_volume.host_path.path
            elif volume_type == 'secret':
                volume_name = k8s_volume.secret.secret_name
            elif volume_type == 'config_map':
                volume_name = k8s_volume.config_map.name
            elif volume_type == 'persistent_volume_claim':
                volume_name = k8s_volume.persistent_volume_claim.claim_name
            volume = VolumeSerializer({
                'name': volume_name,
                'type': volume_type.replace('_', ' '),
                'path': volume_path
            })
            volume_list[k8s_volume.name] = volume.data

        # step through volume mounts
        volume_mount_list = []
        for k8s_volumemount in k8s_container.volume_mounts:
            volume = volume_list.get(k8s_volumemount.name, None)
            if volume and k8s_volumemount.sub_path:
                volume['path'] += k8s_volumemount.sub_path
            vm = VolumeMountSerializer({
                'volume': volume_list.get(k8s_volumemount.name, ""),
                'mount_path': k8s_volumemount.mount_path,
            })
            volume_mount_list.append(vm.data)

        # Create serialized container data
        instance = cls({
            'image': k8s_container.image,
            'volume_mounts': volume_mount_list,
            'name': k8s_container.name})

        return instance


class PodSerializer(serializers.Serializer):
    """
    The API serializer for a pod.
    """
    name = serializers.CharField()
    puid = serializers.CharField(read_only=True)
    creation_timestamp = serializers.DateTimeField(read_only=True)
    start_timestamp = serializers.DateTimeField(read_only=True)
    containers = serializers.ListField(child=ContainerSerializer())
    phase = serializers.CharField(read_only=True)
    reason = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    host_ip = serializers.CharField(read_only=True)
    logs_url = serializers.CharField()

    @classmethod
    def create_from_k8s_pod(cls, k8s_pod):
        container_instances = []
        for k8s_container in k8s_pod.spec.containers:
            instance = ContainerSerializer.create_from_k8s_container(k8s_container, k8s_pod)
            container_instances.append(instance.data)

        kwargs = {
            'version': settings.API_VERSION,
            'puid': k8s_pod.metadata.namespace + "_" + k8s_pod.metadata.name
        }
        pod_instance = cls({
            'name': k8s_pod.metadata.name,
            'puid': k8s_pod.metadata.namespace + "_" + k8s_pod.metadata.name,
            'creation_timestamp': k8s_pod.metadata.creation_timestamp,
            'start_timestamp': k8s_pod.status.start_time,
            'phase': k8s_pod.status.phase if k8s_pod.status.phase else "",
            'reason': k8s_pod.status.reason if k8s_pod.status.reason else "",
            'message': k8s_pod.status.message if k8s_pod.status.message else "",
            'host_ip': k8s_pod.status.host_ip if k8s_pod.status.host_ip else "",
            'containers': container_instances,
            'logs_url': reverse(viewname='pod_logs', kwargs=kwargs)
            })

        return pod_instance


class PodListSerializer(serializers.Serializer):
    pod_urls = serializers.ListField(read_only=True, child=serializers.CharField())


class PodRetrievalView(generics.RetrieveAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pod by its PUID."
    )
    def get(self, request, version, puid):
        namespace, pod_name = puid.split('_')
        pod = api.get_namespaced_pod(namespace, pod_name, request.user)
        if not pod:
            logger.error(f"Pod {pod_name} in namespace {namespace} not found.")
            raise NotFound
        if request.user.has_namespace(namespace):
            container_instances = []
            for k8s_container in pod.spec.containers:
                instance = ContainerSerializer.create_from_k8s_container(k8s_container, pod)
                container_instances.append(instance.data)

            pod_instance = PodSerializer({
                'name': pod.metadata.name,
                'puid': pod.metadata.namespace + "_" + pod.metadata.name,
                'creation_timestamp': pod.metadata.creation_timestamp,
                'start_timestamp': pod.status.start_time,
                'phase': pod.status.phase if pod.status.phase else "",
                'reason': pod.status.reason if pod.status.reason else "",
                'message': pod.status.message if pod.status.message else "",
                'host_ip': pod.status.host_ip if pod.status.host_ip else "",
                'containers': container_instances,
                'logs_url': reverse(viewname='pod_logs', kwargs={ 'version': settings.API_VERSION, 'puid': puid }, request=request)
                })

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
            pods = api.get_namespaced_pods(namespace, request.user)
            puids = [item.metadata.namespace + "_" + item.metadata.name for item in pods]

            instance = PodListSerializer({
                'pod_urls': [reverse(viewname='pod_retrieval', kwargs={'puid': puid}, request=request) for puid in
                             puids] \
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
            return Response(status=api.create_k8s_pod(namespace,
                                                      request.data["name"],
                                                      request.data["containers"],
                                                      request.user))
        else:
            raise NotFound

class PodLogsSerializer(serializers.Serializer):
    hits = serializers.ListField(read_only=True, child=serializers.DictField())
    total = serializers.DictField()
class PodLogsView(generics.RetrieveAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pod logs by its PUID."
    )
    def get(self, request, version, puid):
        namespace, pod_name = puid.split('_')
        if not settings.USE_ELASTIC:
            raise NotAcceptable
        if request.user.has_namespace(namespace):
            client = ElasticSearchClient.get_client()
            if 'page' in request.GET:
                '''
                Pagination of logs
                '''
                page = request.GET['page']
                logs, total = client.get_pod_logs(namespace, pod_name, page)
                pod_logs = PodLogsSerializer({'hits': logs, 'total': total })
                return Response(pod_logs.data)
            else:
                file_path, file_name  = client.create_logs_zip(namespace, pod_name)
                with open(file_path, 'rb') as zip_file:
                    response = HttpResponse(FileWrapper(zip_file), content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
                    zip_file.close()
                    return response
        else:
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{namespace}'. Access denied."
            )
            raise NotFound