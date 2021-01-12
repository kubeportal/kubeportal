from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets, generics
from rest_framework.response import Response


class PodSerializer(serializers.Serializer):
    name = serializers.CharField()


class PodsView(generics.ListAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pods in a namespace."
    )
    def get(self, request):
        return Response(request.user.k8s_pods())

