from django.contrib.auth import get_user_model
from rest_framework import serializers
from kubeportal.models import WebApplication


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class WebApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ('link_name', 'link_url')
