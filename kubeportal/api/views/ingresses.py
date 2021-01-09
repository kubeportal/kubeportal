from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response


class IngressSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    name = serializers.CharField()


class IngressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingresses in the primary namespace of this user."
    )
    def list(self, request, version):
        return Response(request.user.k8s_ingresses())

