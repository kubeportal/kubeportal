from django.contrib.auth import get_user_model
from rest_framework import serializers
from kubeportal.models import WebApplication


class UserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    name = serializers.CharField(source='last_name')
    primary_email = serializers.EmailField(source='email')
    admin = serializers.BooleanField(source='is_staff')
    all_emails = serializers.ListField(source='alt_mails')
    k8s_account = serializers.CharField(source='service_account')
    k8s_namespace = serializers.CharField()
    k8s_token = serializers.CharField(source='token')

    class Meta:
        model = get_user_model()
        fields = (  'firstname',
                    'name',
                    'primary_email',
                    'admin',
                    'all_emails',
                    'k8s_account',
                    'k8s_namespace',
                    'k8s_token',
                    'portal_groups')


class WebApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ('link_name', 'link_url')
