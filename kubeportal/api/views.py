from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.renderers import JSONRenderer
from django.middleware import csrf
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer, WebApplicationSerializer, PortalGroupSerializer
from django.conf import settings
from kubeportal.models.portalgroup import PortalGroup
from kubeportal.models.webapplication import WebApplication
from kubeportal.k8s import kubernetes_api as api

import logging

logger = logging.getLogger('KubePortal')

User = get_user_model()


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
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

    def partial_update(self, request, *args, **kwargs):
        pk = int(self.kwargs['pk'])
        if pk != self.request.user.pk:
            if User.objects.filter(pk=pk).exists():
                raise PermissionDenied
            else:
                raise Http404

        target_user = User.objects.get(pk=pk)
        if len(request.data) == 0:
            logger.warning(f"Got empty body in patch request for user {target_user}.")
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            serializer = UserSerializer(target_user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data=serializer.data, status=200)
            else:
                logger.warning(f"Got invalid body in patch request for user {target_user}.")
                return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class WebApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    '''
    API endpoint that allows for web application(s) to queried.
    '''
    serializer_class = WebApplicationSerializer

    def get_queryset(self):
        if 'user_pk' in self.kwargs:
            # Query for webapp list of a specific user
            # For the moment, a user can only query its own web apps.
            try:
                query_pk = int(self.kwargs['user_pk'])
            except Exception as e:
                logger.error(f'Request failed. Requested user_pk {self.kwargs["user_pk"]} is invalid: {e}')
                return JsonResponse(data='invalid user_pk', status=404)
            if query_pk != self.request.user.pk:
                logger.debug(f"Current user ID is {self.request.user.pk}, denying access to web applications.")
                raise PermissionDenied
            u = User.objects.get(pk=query_pk)
            return u.web_applications(include_invisible=False)

        elif 'pk' in self.kwargs:
            # Query for single webapp, based on the ID
            # Users only get the web applications available for them
            try:
                user_webapp = self.request.user.web_applications(include_invisible=False).filter(pk=self.kwargs['pk'])
            except Exception as e:
                logger.error(f'Request failed. Requested user_pk {self.kwargs["user_pk"]} is invalid: {e}')
                return JsonResponse(data='invalid user_pk', status=404)
            if user_webapp.exists():
                return user_webapp
            else:
                if WebApplication.objects.filter(pk=self.kwargs['pk']).exists():
                    raise PermissionDenied
                else:
                    raise Http404
        else:
            raise Http404


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
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


class ClusterViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    renderer_classes = [JSONRenderer]

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

    def retrieve(self, request, *args, **kwargs):
        key = kwargs['pk']
        if key in self.stats.keys():
            return Response({key: self.stats[key]()})
        else:
            raise NotFound


class K8SResourceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    '''
    Generic base class for fetching a particular Kubernetes resource type for a portal user.
    '''
    renderer_classes = [JSONRenderer]

    def list(self, request, *args, **kwargs):
        if 'user_pk' in self.kwargs:
            try:
                query_pk = int(self.kwargs['user_pk'])
            except Exception as e:
                logger.info(f'Request failed. Requested user_pk {self.kwargs["user_pk"]} is invalid: {e}')
                return JsonResponse(data='invalid user_pk', status=404)
            if query_pk != self.request.user.pk:
                logger.info(f"Permission denied: Current user ID is {self.request.user.pk}, which is different from the requested user ID.")
                raise PermissionDenied
            u = User.objects.get(pk=query_pk)
            return self.list_response(u)
        else:
            raise Http404

class PodViewSet(K8SResourceViewSet):
    def list_response(self, user):
        return Response(user.pods())

class DeploymentViewSet(K8SResourceViewSet):
    def list_response(self, user):
        return Response(user.deployments())

class ServiceViewSet(K8SResourceViewSet):
    def list_response(self, user):
        return Response(user.services())


class BootstrapView(APIView):
    """
    Retreive basic information needed to interact with the API.
    """
    permission_classes = []

    def get(self, request, format=None):
        data = {
            'csrf_token': csrf.get_token(request),
            'portal_version': 'v' + get_kubeportal_version(),
            'default_api_version': settings.API_VERSION
        }
        return Response(data)
