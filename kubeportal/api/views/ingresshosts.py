from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from kubeportal.k8s import kubernetes_api as api
from rest_framework import serializers, generics



class IngressHostListSerializer(serializers.Serializer):
    """
    The API serializer for a list of ingress host names.
    """
    hosts = serializers.ListField(read_only=True, child=serializers.CharField())


class IngressHostsView(GenericAPIView):

    @extend_schema(
        summary="Get the list of host names used by ingresses in all namespaces.",
        responses={200: IngressHostListSerializer}
    )
    def get(self, request, version):
        return Response({'hosts': api.get_ingress_hosts()})
