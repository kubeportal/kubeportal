from rest_framework import serializers, generics
from rest_framework.reverse import reverse

from kubeportal.models.kubernetesnamespace import KubernetesNamespace


class NamespaceSerializer(serializers.ModelSerializer):
    deployments_url = serializers.URLField(read_only=True)
    pods_url = serializers.URLField(read_only=True)
    ingresses_url = serializers.URLField(read_only=True)
    services_url = serializers.URLField(read_only=True)
    persistentvolumeclaims_url = serializers.URLField(read_only=True)

    class Meta:
        model = KubernetesNamespace
        fields = ['name', 'deployments_url', 'pods_url', 'ingresses_url', 'services_url', 'persistentvolumeclaims_url']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context['request']
        ret['deployments_url'] = reverse(viewname='deployments', kwargs={'namespace': instance.name}, request=request)
        ret['pods_url'] = reverse(viewname='pods', kwargs={'namespace': instance.name}, request=request)
        ret['ingresses_url'] = reverse(viewname='ingresses', kwargs={'namespace': instance.name}, request=request)
        ret['services_url'] = reverse(viewname='services', kwargs={'namespace': instance.name}, request=request)
        ret['persistentvolumeclaims_url'] = reverse(viewname='pvcs', kwargs={'namespace': instance.name}, request=request)
        return ret


class NamespaceView(generics.RetrieveAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'namespace'
    serializer_class = NamespaceSerializer
    queryset = KubernetesNamespace.objects.all()

    def get_queryset(self):
        # Clients can only request details of the namespaces that are assigned to them
        return self.request.user.k8s_namespaces()
