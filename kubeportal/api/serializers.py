from dj_rest_auth import serializers as dj_serializers
from django.contrib.auth import get_user_model
from rest_framework import serializers
from kubeportal.models import WebApplication, PortalGroup

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    name = serializers.CharField(source='last_name')
    username = serializers.CharField()
    primary_email = serializers.EmailField(source='email')
    admin = serializers.BooleanField(source='is_staff')
    all_emails = serializers.ListField(source='alt_mails')
    k8s_serviceaccount = serializers.CharField(source='service_account')
    k8s_namespace = serializers.CharField()
    k8s_token = serializers.CharField(source='token')

    class Meta:
        model = User
        fields = ('firstname',
                  'name',
                  'username',
                  'primary_email',
                  'admin',
                  'all_emails',
                  'k8s_serviceaccount',
                  'k8s_namespace',
                  'k8s_token')


class WebApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ('link_name', 'link_url')


class PortalGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalGroup
        fields = ('name', )


class LoginSuccessSerializer(serializers.Serializer):
    '''
    This is an override for the default answer to /login,
    as originally given by the dj_rest_auth library.
    The serializer is referenced in settings.py, accordingly.
    '''
    def to_representation(self, instance):
        return {'id': instance['user'].pk, 'firstname': instance['user'].first_name}
