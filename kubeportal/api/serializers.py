from dj_rest_auth import serializers as dj_serializers
from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.middleware import csrf
from django.conf import settings

from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication

User = get_user_model()

def get_kubeportal_version():
    return settings.VERSION


@extend_schema_serializer(
    examples = [
         OpenApiExample(
            name='Response example',
            value={
                'csrf_token': 'OIiIQkMv5xGfrI75GDAfnm1C1BPxxWlyMgUudmaTBaNKmtulGpSCWQje8uWrQjsb',
                'portal_version': 'v1.1.0',
                'default_api_version': 'v2.0.0'
            },
            response_only=True, 
        ),
    ]
)
class BootstrapInfoSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()
    portal_version = serializers.CharField()
    default_api_version = serializers.CharField()

    @staticmethod
    def get_response(request):
        return {
            'csrf_token': csrf.get_token(request),
            'portal_version': 'v' + get_kubeportal_version(),
            'default_api_version': settings.API_VERSION
        }


class ClusterInfoSerializer(serializers.Serializer):

    @staticmethod
    def get_response(request, info_slug):
        stats = {'k8s_version': api.get_kubernetes_version,
                 'k8s_apiserver_url': api.get_apiserver,
                 'k8s_node_count': api.get_number_of_nodes,
                 'k8s_cpu_count': api.get_number_of_cpus,
                 'k8s_mem_sum': api.get_memory_sum,
                 'k8s_pod_count': api.get_number_of_pods,
                 'k8s_volume_count': api.get_number_of_volumes,
                 'portal_user_count': get_user_count,
                 'portal_version': get_kubeportal_version,
                 'k8s_cluster_name': get_cluster_name,
                 }

        if info_slug in stats.keys():
            return {info_slug: self.stats[info_slug]()}
        else:
            raise NotFound


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


class IngressHostsSerializer(serializers.Serializer):
    pass

class PodSerializer(serializers.Serializer):
    pass

class DeploymentSerializer(serializers.Serializer):
    pass

class ServiceSerializer(serializers.Serializer):
    pass

class IngressSerializer(serializers.Serializer):
    pass


class LoginSuccessSerializer(serializers.Serializer):
    """
    This is an override for the default answer to /login,
    as originally given by the dj_rest_auth library.
    The serializer is referenced in settings.py, accordingly.
    """

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        return {'id': instance['user'].pk,
                'firstname': instance['user'].first_name,
                'access_token': str(instance['access_token'])
                }
