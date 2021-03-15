from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_serializer
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


class AnnotationSerializer(serializers.Serializer):
    """
    The API serializer for a annotation definition.
    """
    key = serializers.CharField()
    value = serializers.CharField()


class IngressPathSerializer(serializers.Serializer):
    path = serializers.CharField()
    service_name = serializers.CharField()
    service_port = serializers.IntegerField()


class IngressRuleSerializer(serializers.Serializer):
    """
    The API serializer for a ingress rule definition.
    """
    host = serializers.CharField()
    paths = serializers.ListField(child=IngressPathSerializer())


class IngressSerializer(serializers.Serializer):
    """
    The API serializer for an ingress definition.
    """
    name = serializers.CharField()
    annotations = serializers.ListField(child=AnnotationSerializer())
    tls = serializers.BooleanField()
    rules = serializers.ListField(child=IngressRuleSerializer())
    creation_timestamp = serializers.DateTimeField(read_only=True)


class IngressListSerializer(serializers.Serializer):
    """
    The API serializer for a list of ingresses.
    """
    deployment_urls = serializers.ListField(read_only=True, child=serializers.URLField())


class IngressRetrievalView(generics.RetrieveAPIView):
    serializer_class = IngressSerializer


class IngressesView(generics.ListCreateAPIView):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingresses in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(api.get_namespaced_ingresses(namespace))
        else:
            # https://lockmedown.com/when-should-you-return-404-instead-of-403-http-status-code/
            raise NotFound

    @extend_schema(
        summary="Create an ingress in a namespace."
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_ingress(namespace,
                                   request.data["name"],
                                   request.data["annotations"],
                                   request.data["tls"],
                                   request.data["rules"]
                                   )
            return Response(status=201)
        else:
            raise NotFound
