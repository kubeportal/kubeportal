from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer


from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer, WebApplicationSerializer
from kubeportal.models import WebApplication
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
    queryset = WebApplication.objects.all()
    serializer_class = WebApplicationSerializer


def get_user_count():
    User = get_user_model()
    return User.objects.count()


def get_kubeportal_version():
    return settings.VERSION


class StatisticsView(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]

    stats = {'kubernetes_version': kubernetes.get_kubernetes_version,
             'apiserver_url': kubernetes.get_apiserver,
             'node_count': kubernetes.get_number_of_nodes,
             'cpu_count': kubernetes.get_number_of_cpus,
             'mainmemory_sum': kubernetes.get_memory_sum,
             'pod_count': kubernetes.get_number_of_pods,
             'volume_count': kubernetes.get_number_of_volumes,
             'user_count': get_user_count,
             'kubeportal_version': get_kubeportal_version}

    def retrieve(self, request, *args, **kwargs):
        key = kwargs['pk']
        if key in self.stats.keys():
            return Response({'value': self.stats[key]()})
        else:
            raise NotFound

    def list(self, request, *args, **kwargs):
        return Response(self.stats.keys())

    def get_queryset(self):
        return None


