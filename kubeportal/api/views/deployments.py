from drf_spectacular.utils import extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from kubeportal.k8s import kubernetes_api as api


class DeploymentSerializer(serializers.Serializer):
    name = serializers.CharField()
    replicas = serializers.IntegerField()
    creation_timestamp = serializers.DateTimeField(read_only=True)


class DeploymentsView(generics.ListCreateAPIView):
    serializer_class = DeploymentSerializer

    @extend_schema(
        summary="Get deployments in a namespace."
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            return Response(api.get_namespaced_deployments(namespace))
        else:
            # https://lockmedown.com/when-should-you-return-404-instead-of-403-http-status-code/
            raise NotFound



    @extend_schema(
        summary="Create a deployment in a namespace."
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_deployment(namespace,
                                      request.data["name"],
                                      request.data["replicas"],
                                      request.data["matchLabels"],
                                      request.data["template"])
            return Response(status=201)
        else:
            raise NotFound
