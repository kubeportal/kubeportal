from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.generics import RetrieveAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer
from django.middleware import csrf
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.contrib.auth import get_user_model
from kubeportal.api import serializers
from django.conf import settings
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.k8s import kubernetes_api as api


import logging

logger = logging.getLogger('KubePortal')

User = get_user_model()


def get_user_count():
    return User.objects.count()

def get_kubeportal_version():
    return settings.VERSION



def get_cluster_name():
    return settings.BRANDING


class BootstrapInfoView(APIView):
    """
    Get bootstrap information for talking to this API.
    """
    permission_classes = []
    serializer_class = serializers.BootstrapInfoSerializer # only for drf_spectacular

    def get(self, request, format=None):
        return Response(serializers.BootstrapInfoSerializer.get_response(request))

class ClusterInfoView(APIView):
    """
    Get information about the Kubernetes cluster.
    """
    permission_classes = []
    serializer_class = serializers.ClusterInfoSerializer # only for drf_spectacular

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='info_slug',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='Information to be retrieved',
                enum = []
            ),
        ]
    )
    def get(self, request, info_slug):
        return Response(serializers.ClusterInfoSerializer.get_response(request, info_slug))


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows access to the registered portal users.
    """
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        """
        Clients can only request details of the user that they used for login.
        """
        return User.objects.filter(pk=self.request.user.pk)


class WebApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for web application(s) to queried.
    """
    serializer_class = serializers.WebApplicationSerializer

    def get_queryset(self):
        """
        Users can only request details of their own web applications.
        """
        return self.request.user.web_applications(include_invisible=False)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows for groups to queried
    """
    serializer_class = serializers.PortalGroupSerializer

    def get_queryset(self):
        """
        Users can only request details of their own user groups.
        """
        return self.request.user.portal_groups.all()



class PodViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    List Kubernetes pods in the user namespaces.
    """
    renderer_classes = [JSONRenderer]
    queryset = WebApplication.objects.none()
    serializer_class = serializers.PodSerializer

    def list(self, request, *args, **kwargs):
        return Response(request.user.k8s_pods())


class DeploymentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Manage Kubernetes deployments in the user namespaces.
    """
    renderer_classes = [JSONRenderer]
    queryset = WebApplication.objects.none()
    serializer_class = serializers.DeploymentSerializer

    def list(self, request, *args, **kwargs):
        return Response(request.user.k8s_deployments())

    def create(self, request, *args, **kwargs):
        api.create_k8s_deployment(  request.user.k8s_namespace().name, 
                                    params["name"], 
                                    params["replicas"],
                                    params["matchLabels"], 
                                    params["template"])
        return Response(status=201)


class ServiceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    List Kubernetes services in the user namespaces.
    """
    renderer_classes = [JSONRenderer]
    queryset = WebApplication.objects.none()
    serializer_class = serializers.ServiceSerializer

    def list(self, request, *args, **kwargs):
        return Response(request.user.k8s_services())


class IngressViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    List Kubernetes ingresses in the user namespaces.
    """
    renderer_classes = [JSONRenderer]
    queryset = WebApplication.objects.none()
    serializer_class = serializers.IngressSerializer

    def list(self, request, *args, **kwargs):
        return Response(request.user.k8s_ingresses())


class IngressHostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    List hosts being used for ingresses across all cluster namespaces.
    """
    renderer_classes = [JSONRenderer]
    serializer_class = serializers.IngressHostsSerializer

    def list(self, request, *args, **kwargs):
        return Response(api.get_ingress_hosts())

