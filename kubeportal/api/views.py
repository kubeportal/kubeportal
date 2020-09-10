from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer, WebApplicationSerializer, PortalGroupSerializer
from kubeportal.models import WebApplication, PortalGroup
from kubeportal import kubernetes
from django.conf import settings
import logging

logger = logging.getLogger('KubePortal')

User = get_user_model()

class UserView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that allows for users to queried
    '''
    serializer_class = UserSerializer

    def get_queryset(self):
        query_pk = int(self.kwargs['pk'])
        if query_pk == self.request.user.pk:
            return User.objects.filter(pk=query_pk)   
        else:
            if User.objects.filter(pk=query_pk).exists():
                raise PermissionDenied
            else:
                raise Http404


class WebApplicationView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for web application(s) to queried.
    '''
    serializer_class = WebApplicationSerializer

    def get_queryset(self):
        if 'user_pk' in self.kwargs:
            # Query for webapp list of a specific user
            # For the moment, a user can only query its own web apps.
            query_pk = int(self.kwargs['user_pk'])
            if query_pk != self.request.user.pk:
                logger.debug(f"Current user ID is {self.request.user.pk}, denying access to web applications.")
                raise PermissionDenied
            u = User.objects.get(pk=query_pk)
            return u.web_applications(include_invisible=False)

        elif 'pk' in self.kwargs:
            # Query for single webapp, based on the ID
            # Users only get the web applications available for them
            user_webapp = self.request.user.web_applications(include_invisible=False).filter(pk=self.kwargs['pk'])
            if user_webapp.exists():
                return user_webapp
            else:
                if WebApplication.objects.filter(pk=self.kwargs['pk']).exists():
                    raise PermissionDenied
                else:
                    raise Http404
        else:
            raise Http404

class GroupView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for groups to queried
    '''
    serializer_class = PortalGroupSerializer

    def get_queryset(self):
        if 'user_pk' in self.kwargs:
            # Query for group list of a specific user
            # For the moment, a user can only query its own groups.
            query_pk = int(self.kwargs['user_pk'])
            if query_pk != self.request.user.pk:
                logger.debug(f"Current user ID is {self.request.user.pk}, denying access to groups.")
                raise PermissionDenied
            u = User.objects.get(pk=query_pk)
            return u.portal_groups.all()

        elif 'pk' in self.kwargs:
            # Query for single group, based on the ID
            # Users only get the groups assigned to them
            group = self.request.user.portal_groups.filter(pk=self.kwargs['pk'])
            if group.exists():
                return group
            else:
                if PortalGroup.objects.filter(pk=self.kwargs['pk']).exists():
                    raise PermissionDenied
                else:
                    raise Http404
        else:
            raise Http404


def get_user_count():
    return User.objects.count()


def get_kubeportal_version():
    return settings.VERSION


def get_cluster_name():
    return settings.BRANDING


class ClusterView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]

    stats = {'k8s_version': kubernetes.get_kubernetes_version,
             'k8s_apiserver_url': kubernetes.get_apiserver,
             'k8s_node_count': kubernetes.get_number_of_nodes,
             'k8s_cpu_count': kubernetes.get_number_of_cpus,
             'k8s_mem_sum': kubernetes.get_memory_sum,
             'k8s_pod_count': kubernetes.get_number_of_pods,
             'k8s_volume_count': kubernetes.get_number_of_volumes,
             'portal_user_count': get_user_count,
             'portal_version': get_kubeportal_version,
             'k8s_cluster_name': get_cluster_name}

    def retrieve(self, request, *args, **kwargs):
        key = kwargs['pk']
        if key in self.stats.keys():
            return Response({'value': self.stats[key]()})
        else:
            raise NotFound

    def get_queryset(self):
        return None
