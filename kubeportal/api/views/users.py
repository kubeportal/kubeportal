import urllib

from django.urls import resolve
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
import logging

from rest_framework.reverse import reverse

logger = logging.getLogger('KubePortal')

from kubeportal.api.views.tools import User


class RestrictedUserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(read_only=True, source='first_name')
    name = serializers.CharField(read_only=True, source='last_name')
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ('firstname',
                  'name',
                  'user_id')


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
    namespace_names = serializers.ListField(read_only=True, 
                                            child=serializers.CharField(),
                                            source='k8s_namespace_names')
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
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'

    def get_serializer_class(self):
        if 'user_id' not in self.kwargs:
            # Generic question for the serializer by the Swagger docs page.
            return UserSerializer
        if self.request.user.pk == self.kwargs['user_id']:
            # User requests her own information, gets full access
            return UserSerializer
        else:
            if self.request.method == "GET":
                # user requests information for somebody else (news, approval admins, ...), only gets names
                return RestrictedUserSerializer
            else:
                # Anything but GET for another user is not allowed
                raise NotFound


class UserApprovalSerializer(serializers.Serializer):
    state = serializers.ChoiceField(read_only=True, choices=("NEW", "ACCESS_REQUESTED", "ACCESS_REJECTED", "ACCESS_APPROVED"))
    approving_admin_urls = serializers.ListField(read_only=True, child=serializers.URLField())
    approving_admin_url = serializers.URLField(write_only=True)


class UserApprovalView(generics.RetrieveAPIView, generics.CreateAPIView):
    serializer_class = UserApprovalSerializer

    @extend_schema(
        summary="Get the approval status of a user."
    )
    def get(self, request, version, user_id):
        if request.user.pk == user_id:
            instance = UserApprovalSerializer({
                'state': request.user.state,
                'approving_admin_urls': [reverse(viewname='user', kwargs={'user_id': u.pk}, request=request) for u in User.objects.filter(is_superuser=True)]
            })
            return Response(instance.data)
        else:
            logger.error(f"User {request.user} is not allowed to fetch the approval status fpr user id {user_id}.")
            raise NotFound

    @extend_schema(
        summary="Request approval for this user.",
    )
    def post(self, request, version, user_id):
        admin_url = request.data["approving_admin_url"]
        path = urllib.parse.urlparse(admin_url).path
        resolved_func, unused_args, resolved_kwargs = resolve(path)
        admin_user = resolved_func.cls().get_queryset().get(pk=resolved_kwargs['user_id'])
        if request.user.send_access_request(request, administrator=admin_user):
            return Response(status=202)
        else:
            return Response(status=500)
