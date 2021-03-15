from rest_framework import serializers, generics

from kubeportal.models.kubernetesserviceaccount import KubernetesServiceAccount


class ServiceAccountSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    uid = serializers.CharField(read_only=True)
    namespace = serializers.HyperlinkedRelatedField(view_name='namespace', lookup_field='name', lookup_url_kwarg='namespace', read_only=True)


    class Meta:
        model = KubernetesServiceAccount
        fields = ['name', 'uid', 'namespace']


class ServiceAccountRetrievalView(generics.RetrieveAPIView):
    lookup_field = 'uid'
    serializer_class = ServiceAccountSerializer

    def get_queryset(self):
        # Clients can only request details of the service accounts that are assigned to them
        return self.request.user.k8s_accounts()


