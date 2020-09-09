from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer


from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer, WebApplicationSerializer, PortalGroupSerializer
from kubeportal.models import WebApplication, PortalGroup
from kubeportal import kubernetes
from django.conf import settings


class UserView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that allows for users to queried
    '''
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return get_user_model().objects.filter(pk=self.request.user.pk)


class WebApplicationView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for web applications to queried

    @todo: Implement web application filtering
    '''
    serializer_class = WebApplicationSerializer

    def get_queryset(self):
        return self.request.user.web_applications()


class GroupView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for groups to queried

    @todo: Implement web application filtering
    '''
    queryset = PortalGroup.objects.all()
    serializer_class = PortalGroupSerializer


def get_user_count():
    User = get_user_model()
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
            return Response(self.stats[key]())
        else:
            raise NotFound

    def get_queryset(self):
        return None
