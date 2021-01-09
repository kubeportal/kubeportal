from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response


class IngressSerializer(serializers.Serializer):
    name = serializers.CharField()


class IngressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingresses in the primary namespace of this user."
    )
    def list(self, request, version):
        return Response(request.user.k8s_ingresses())

