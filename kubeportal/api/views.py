from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer
from kubeportal.models import UserState
from kubeportal import kubernetes
from django.conf import settings


class UserView(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for users to queried
    '''
    queryset = get_user_model().objects.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer


class KubeportalStatisticsView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that returns statistics for the Kubeportal installation.
    '''
    def retrieve(request, *args, **kwargs):
        # Production tests have shown that some of these Kubernetes calls may take a moment.
        # Given that, we offer individual API endpoints per single statistic and let the frontend
        # fetch the stuff async.

        key = kwargs['pk']
        if key == 'user_count':
            User = get_user_model()
            return Response(User.objects.count())
        if key == 'version':
            return Response(settings.VERSION)

        raise NotFound

class ClusterStatisticsView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that returns statistics for the whole cluster.
    '''
    def retrieve(request, *args, **kwargs):
        # Production tests have shown that some of these Kubernetes calls may take a moment.
        # Given that, we offer individual API endpoints per single statistic and let the frontend
        # fetch the stuff async.

        key = kwargs['pk']
        if key == 'kubernetes_version':
            return Response(kubernetes.get_kubernetes_version())
        if key == 'apiserver_url':
            return Response(kubernetes.get_apiserver())
        if key == 'node_count':
            return Response(kubernetes.get_number_of_nodes())
        if key == 'cpu_count':
            return Response(kubernetes.get_number_of_cpus())
        if key == 'mainmemory_sum':
            return Response(kubernetes.get_memory_sum())
        if key == 'pod_count':
            return Response(kubernetes.get_number_of_pods())
        if key == 'volume_count':
            return Response(kubernetes.get_number_of_volumes())

        raise NotFound
