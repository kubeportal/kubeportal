from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import serializers, mixins, viewsets, generics

from kubeportal.api.views.tools import User


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only = True)
    group_ids = serializers.ListField(read_only = True,
        child = serializers.IntegerField()
    )
    webapp_ids = serializers.ListField(read_only = True,
        child = serializers.IntegerField()
    )
    firstname = serializers.CharField(source='first_name')
    name = serializers.CharField(source='last_name')
    username = serializers.CharField(read_only = True)
    primary_email = serializers.EmailField(source='email')
    admin = serializers.BooleanField(source='is_staff', read_only = True)
    all_emails = serializers.ListField(read_only = True)
    k8s_serviceaccount = serializers.CharField(source='service_account', read_only = True)
    k8s_namespace = serializers.CharField(read_only = True)
    k8s_token = serializers.CharField(source='token', read_only = True)

    class Meta:
        model = User
        fields = ('user_id',
                  'group_ids',
                  'webapp_ids',
                  'firstname',
                  'name',
                  'username',
                  'primary_email',
                  'admin',
                  'all_emails',
                  'k8s_serviceaccount',
                  'k8s_namespace',
                  'k8s_token')


@extend_schema_view(
    retrieve=extend_schema(summary='Get attributes of this user.'),
    update=extend_schema(summary='Overwrite attributes of this user.'),
    partial_update=extend_schema(summary='Modify single attributes of this user.')
)
class UserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        # Clients can only request details of the user that they used for login.
        return User.objects.filter(pk=self.request.user.pk)
