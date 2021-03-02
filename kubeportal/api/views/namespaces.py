from rest_framework import serializers, generics

from kubeportal.models.kubernetesnamespace import KubernetesNamespace


class NamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KubernetesNamespace
        fields = ['name', ]


class NamespaceView(generics.RetrieveAPIView):
    lookup_field = 'name'
    lookup_url_kwarg = 'namespace'
    serializer_class = NamespaceSerializer
    queryset = KubernetesNamespace.objects.all()

    def get_queryset(self):
        # Clients can only request details of the namespaces that are assigned to them
        return self.request.user.k8s_namespaces()
