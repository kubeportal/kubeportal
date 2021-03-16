from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import serializers, generics

from kubeportal.api.views.tools import User


class UserSerializer(serializers.ModelSerializer):
    group_urls = serializers.HyperlinkedRelatedField(many=True,
                                                     view_name='group',
                                                     lookup_url_kwarg='group_id',
                                                     read_only=True,
                                                     source='portal_groups')
    webapp_urls = serializers.HyperlinkedRelatedField(many=True,
                                                      view_name='webapplication',
                                                      lookup_url_kwarg='webapp_id',
                                                      read_only=True,
                                                      source='webapps')
    firstname = serializers.CharField(source='first_name')
    name = serializers.CharField(source='last_name')
    state = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    primary_email = serializers.EmailField(source='email')
    admin = serializers.BooleanField(source='is_staff', read_only=True)
    all_emails = serializers.ListField(read_only=True)
    serviceaccount_urls = serializers.HyperlinkedRelatedField(many=True,
                                                              view_name='serviceaccount_retrieval',
                                                              lookup_url_kwarg='uid',
                                                              lookup_field='uid',
                                                              read_only=True,
                                                              source='k8s_accounts')
    namespace_urls = serializers.HyperlinkedRelatedField(many=True,
                                                         view_name='namespace',
                                                         lookup_url_kwarg='namespace',
                                                         lookup_field='name',
                                                         read_only=True,
                                                         source='k8s_namespaces')
    namespace_names = serializers.ListField(read_only=True)
    k8s_token = serializers.CharField(source='token', read_only=True)

    class Meta:
        model = User
        fields = ('group_urls',
                  'webapp_urls',
                  'firstname',
                  'name',
                  'username',
                  'user_id',
                  'primary_email',
                  'admin',
                  'state',
                  'all_emails',
                  'serviceaccount_urls',
                  'namespace_urls',
                  'namespace_names',
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
