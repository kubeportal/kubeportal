from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer, WebApplicationSerializer
from kubeportal.models import UserState, WebApplication
from kubeportal import kubernetes
from django.conf import settings


class UserView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for users to queried
    '''
    queryset = get_user_model().objects.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer


class WebApplicationView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for web applications to queried

    @todo: Implement web application filtering
    '''
    queryset = WebApplication.objects.all()
    serializer_class = WebApplicationSerializer


class KubeportalStatisticsView(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that returns statistics for the Kubeportal installation.
    '''
    def retrieve(request, *args, **kwargs):
        key = kwargs['pk']
        if key == 'user_count':
            User = get_user_model()
            return Response(User.objects.count())
        if key == 'version':
            return Response(settings.VERSION)

        raise NotFound

    def list(request, *args, **kwargs):
        return Response(['user_count', 'version'])

    def get_queryset(self):
        return None


class ClusterStatisticsView(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that returns statistics for the whole cluster.
    '''

    stats = {'kubernetes_version': kubernetes.get_kubernetes_version,
             'apiserver_url': kubernetes.get_apiserver,
             'node_count': kubernetes.get_number_of_nodes,
             'cpu_count': kubernetes.get_number_of_cpus,
             'mainmemory_sum': kubernetes.get_memory_sum,
             'pod_count': kubernetes.get_number_of_pods,
             'volume_count': kubernetes.get_number_of_volumes}

    def retrieve(self, request, *args, **kwargs):
        # Production tests have shown that some of these Kubernetes calls may take a moment.
        # Given that, we offer individual API endpoints per single statistic and let the frontend
        # fetch the stuff async.

        key = kwargs['pk']
        if key in self.stats.keys():
            return Response(self.stats[key]())
        else:
            raise NotFound

    def list(request, *args, **kwargs):
        return Response(['kubernetes_version', 'apiserver_url', 'node_count', 'cpu_count', 'mainmemory_sum', 'pod_count', 'volume_count'])

    def get_queryset(self):
        return None
