from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


class StorageClassListSerializer(serializers.Serializer):
    """
    The API serializer for a list of storage classes.
    """
    classes = serializers.ListField(read_only=True, child=serializers.CharField())


class StorageClassesView(GenericAPIView):

    @extend_schema(
        summary="Get the list of storage classes supported in this cluster.",
        responses={200: StorageClassListSerializer}
    )
    def get(self, request, version):
        return Response({'classes': [item.metadata.name for item in api.get_storageclasses()]})
