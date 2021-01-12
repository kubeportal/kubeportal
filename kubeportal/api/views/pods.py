from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response


class PodSerializer(serializers.Serializer):
    name = serializers.CharField()


class PodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pods in a namespace."
    )
    def list(self, request, version):
        return Response(request.user.k8s_pods())

