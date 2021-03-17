import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api
from .pods import ContainerSerializer

logger = logging.getLogger('KubePortal')


class PersistentVolumeClaimListSerializer(serializers.Serializer):
    persistentvolumeclaim_urls = serializers.ListField(child=serializers.URLField(), read_only=True)

class PersistentVolumeClaimSerializer(serializers.Serializer):
    """
    The API serializer for a single PVC.
    """
    name = serializers.CharField()
    uid = serializers.CharField(read_only=True)
    creation_timestamp = serializers.DateTimeField(read_only=True)
    access_modes = serializers.ListField(
                    child=serializers.ChoiceField(
                        choices=("ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany")))
    storage_class_name = serializers.CharField()
    volume_name = serializers.CharField(read_only=True)
    size = serializers.CharField()
    phase = serializers.CharField(read_only=True)

class PersistentVolumeClaimRetrievalView(generics.RetrieveAPIView):
    serializer_class = PersistentVolumeClaimSerializer

    @extend_schema(
        summary="Get persistent volume claim by its UID."
    )
    def get(self, request, version, uid):
        pvc = api.get_pvc(uid)

        if not request.user.has_namespace(pvc.metadata.namespace):
            logger.warning(
                f"User '{request.user}' has no access to the namespace '{deployment.metadata.namespace}' of pvc '{pvc.metadata.uid}'. Access denied.")
            raise NotFound

        if pvc.status.capacity:
            capacity = pvc.status.capacity['storage']
        else:
            capacity = None

        if pvc.status.access_modes:
            access_modes = pvc.status.access_modes
        else:
            access_modes = pvc.spec.access_modes

        instance = PersistentVolumeClaimSerializer({
            'name': pvc.metadata.name,
            'uid': pvc.metadata.uid,
            'creation_timestamp': pvc.metadata.creation_timestamp,
            'access_modes': access_modes,
            'storage_class_name': pvc.spec.storage_class_name,
            'volume_name': pvc.spec.volume_name,
            'size': capacity,
            'phase': pvc.status.phase
        })
        return Response(instance.data)


class PersistentVolumeClaimsView(generics.RetrieveAPIView, generics.CreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return PersistentVolumeClaimSerializer
        if self.request.method == "POST":
            return PersistentVolumeClaimListSerializer

    @extend_schema(
        summary="Get the list of persistent volume claims in a namespace.",
        request=None,
        responses=PersistentVolumeClaimListSerializer
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            pvcs = api.get_namespaced_pvcs(namespace)
            uids = [item.metadata.uid for item in pvcs]
            instance = PersistentVolumeClaimListSerializer({
                'persistentvolumeclaim_urls': [reverse(viewname='pvc_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]\
            })

            return Response(instance.data)
        else:
            raise NotFound

    @extend_schema(
        summary="Create a persistent volume claim in a namespace.",
        request=PersistentVolumeClaimSerializer,
        responses=None
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_pvc(namespace,
                               request.data["name"],
                               request.data["access_modes"],
                               request.data.get("storage_class_name", None),
                               request.data["size"])
            return Response(status=201)
        else:
            raise NotFound

