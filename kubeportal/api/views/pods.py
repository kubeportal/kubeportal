from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


class PodSerializer(serializers.Serializer):
    name = serializers.CharField()


class PodView(generics.RetrieveAPIView):
    serializer_class = PodSerializer



class PodsView(generics.ListAPIView):
    serializer_class = PodSerializer

    @extend_schema(
        summary="Get pods in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(api.get_namespaced_pods(namespace))
        else:
            raise NotFound
