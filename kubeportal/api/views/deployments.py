from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets, generics
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
    def get(self, request):
        return Response(request.user.k8s_deployments())

    @extend_schema(
        summary="Create a deployment in a namespace."
    )
    def post(self, request):
        api.create_k8s_deployment(request.user.k8s_namespace().name,
                                  request.data["name"],
                                  request.data["replicas"],
                                  request.data["matchLabels"],
                                  request.data["template"])
        return Response(status=201)
