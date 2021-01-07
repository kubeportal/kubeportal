from drf_spectacular.utils import extend_schema
from rest_framework import serializers, mixins, viewsets
from rest_framework.response import Response


class DeploymentSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    name = serializers.CharField()
    replicas = serializers.IntegerField()
    creation_timestamp = serializers.DateTimeField(read_only=True)


class DeploymentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = DeploymentSerializer

    @extend_schema(
        summary="Get deployments in the primary namespace of this user."
    )
    def list(self, request):
        return Response(request.user.k8s_deployments())

    @extend_schema(
        summary="Create a deployment in the primary namespace of this user."
    )
    def create(self, request):
        #         # api.create_k8s_deployment(request.user.k8s_namespace().name,
        #         #                          params["name"],
        #         #                         params["replicas"],
        #         #                                  params["matchLabels"],
        #         #                                  params["template"])
        return Response(status=201)
