from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response


class ServiceSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    name = serializers.CharField()


class ServiceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ServiceSerializer

    @extend_schema(
        summary="Get services in the primary namespace of this user."
    )
    def list(self, request, version):
        return Response(request.user.k8s_services())

