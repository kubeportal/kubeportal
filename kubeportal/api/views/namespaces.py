from rest_framework import serializers, generics
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from drf_spectacular.types import OpenApiTypes

from kubeportal.models.kubernetesnamespace import KubernetesNamespace

class DeploymentListSerializer(serializers.Serializer):
    """
    The API serializer for a list of deployments.
    """
    deployment_urls = serializers.ListField(read_only=True, child=serializers.URLField())


class PodListSerializer(serializers.Serializer):
    """
    The API serializer for a list of pods.
    """
    pod_urls = serializers.ListField(read_only=True, child=serializers.URLField())


class IngressListSerializer(serializers.Serializer):
    """
    The API serializer for a list of ingresses.
    """
    ingress_urls = serializers.ListField(read_only=True, child=serializers.URLField())

class ServiceListSerializer(serializers.Serializer):
    """
    The API serializer for a list of services.
    """
    service_urls = serializers.ListField(read_only=True, child=serializers.URLField())


class ServiceAccountListSerializer(serializers.Serializer):
    """
    The API serializer for a list of service accounts.
    """
    service_account_urls = serializers.HyperlinkedRelatedField(many=True, view_name='serviceaccount', lookup_url_kwarg='uid', lookup_field='service_accounts', read_only=True)


class NamespaceLinksSerializer(DeploymentListSerializer, PodListSerializer, ServiceAccountListSerializer, ServiceListSerializer, IngressListSerializer):
    pass

class NamespaceSerializer(serializers.ModelSerializer):
    links = NamespaceLinksSerializer()

    class Meta:
        model = KubernetesNamespace
        fields = ['name', 'links']

    @extend_schema_field(PodListSerializer)
    def get_pod_urls(self, obj):
        uids = obj.get_pod_uids()
        request = self.context['request']        
        return [reverse(viewname='pod', kwargs={'uid': uid}, request=request) for uid in uids]

    @extend_schema_field(DeploymentListSerializer)
    def get_deployment_urls(self, obj):        
        uids = obj.get_deployment_uids()
        request = self.context['request']        
        return [reverse(viewname='deployment', kwargs={'uid': uid}, request=request) for uid in uids]

    @extend_schema_field(ServiceAccountListSerializer)
    def get_service_account_urls(self, obj):        
        uids = obj.get_deployment_uids()
        request = self.context['request']        
        return [reverse(viewname='deployment', kwargs={'uid': uid}, request=request) for uid in uids]

    @extend_schema_field(IngressListSerializer)
    def get_ingress_urls(self, obj):        
        uids = obj.get_ingress_uids()
        request = self.context['request']        
        return [reverse(viewname='ingress', kwargs={'uid': uid}, request=request) for uid in uids]

    @extend_schema_field(ServiceListSerializer)
    def get_service_urls(self, obj):        
        uids = obj.get_service_uids()
        request = self.context['request']        
        return [reverse(viewname='service', kwargs={'uid': uid}, request=request) for uid in uids]


class NamespaceView(generics.RetrieveAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'namespace'
    serializer_class = NamespaceSerializer
    queryset = KubernetesNamespace.objects.all()

    def get_queryset(self):
        # Clients can only request details of the namespaces that are assigned to them
        return self.request.user.k8s_namespaces()
