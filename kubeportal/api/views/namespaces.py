from rest_framework import serializers, generics
from rest_framework.reverse import reverse

from kubeportal.models.kubernetesnamespace import KubernetesNamespace


class NamespaceSerializer(serializers.ModelSerializer):
    deployment_urls = serializers.ListField(child=serializers.URLField(), read_only=True)
    pod_urls = serializers.ListField(child=serializers.URLField(), read_only=True)
    ingress_urls = serializers.ListField(child=serializers.URLField(), read_only=True)
    service_urls = serializers.ListField(child=serializers.URLField(), read_only=True)
    service_account_urls = serializers.HyperlinkedRelatedField(many=True,
                                                               view_name='serviceaccount_retrieval',
                                                               lookup_url_kwarg='uid',
                                                               source='service_accounts',
                                                               lookup_field='uid',
                                                               read_only=True)

    class Meta:
        model = KubernetesNamespace
        fields = ['name', 'deployment_urls', 'pod_urls', 'ingress_urls', 'service_urls', 'service_account_urls']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['deployment_urls'] = self.get_deployment_urls(instance)
        ret['pod_urls'] = self.get_pod_urls(instance)
        ret['ingress_urls'] = self.get_ingress_urls(instance)
        ret['service_urls'] = self.get_service_urls(instance)
        return ret

    def get_deployment_urls(self, obj):
        uids = obj.get_deployment_uids()
        request = self.context['request']
        return [reverse(viewname='deployment_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]

    def get_pod_urls(self, obj):
        uids = obj.get_pod_uids()
        request = self.context['request']
        return [reverse(viewname='pod_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]

    def get_ingress_urls(self, obj):
        uids = obj.get_ingress_uids()
        request = self.context['request']
        return [reverse(viewname='ingress_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]

    def get_service_urls(self, obj):
        uids = obj.get_service_uids()
        request = self.context['request']
        return [reverse(viewname='service_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]


class NamespaceView(generics.RetrieveAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'namespace'
    serializer_class = NamespaceSerializer
    queryset = KubernetesNamespace.objects.all()

    def get_queryset(self):
        # Clients can only request details of the namespaces that are assigned to them
        return self.request.user.k8s_namespaces()
