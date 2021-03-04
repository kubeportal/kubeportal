from rest_framework import serializers, generics
from rest_framework.reverse import reverse

from kubeportal.models.kubernetesnamespace import KubernetesNamespace


class NamespaceSerializer(serializers.ModelSerializer):
    pods = serializers.SerializerMethodField()
    deployments = serializers.SerializerMethodField()

    class Meta:
        model = KubernetesNamespace
        fields = ['name', 'pods', 'deployments']

    def get_pods(self, obj):        
        uids = obj.get_pod_uids()
        request = self.context['request']        
        return [reverse(viewname='pod', kwargs={'uid': uid}, request=request) for uid in uids]

    def get_deployments(self, obj):        
        uids = obj.get_deployment_uids()
        request = self.context['request']        
        return [reverse(viewname='deployment', kwargs={'uid': uid}, request=request) for uid in uids]


class NamespaceView(generics.RetrieveAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'namespace'
    serializer_class = NamespaceSerializer
    queryset = KubernetesNamespace.objects.all()

    def get_queryset(self):
        # Clients can only request details of the namespaces that are assigned to them
        return self.request.user.k8s_namespaces()
