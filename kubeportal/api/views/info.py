from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.reverse import reverse


from kubeportal.api.views.tools import get_user_count, get_kubeportal_version, get_cluster_name
from kubeportal.k8s import kubernetes_api as api

class InfoDetailView(GenericAPIView):
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

    @extend_schema(
        operation={
            "operationId": "get_info",
            "tags": ["api"],
            "summary": "Get information about the portal and the cluster.",
            "security": [{"jwtAuth": []}],
            "parameters": [{
                "in": "path",
                "name": "info_slug",
                "required": "true",
                "schema": {
                    "type": "string",
                    "enum": [
                        "portal_user_count",  # Number of portal users registered
                        "portal_version",  # Version of the portal software
                        "k8s_version",  # Version of the Kubernetes installation
                        "k8s_node_count",  # Number of Kubernetes nodes
                        "k8s_cpu_count",  # Number of CPU cores in Kubernetes
                        "k8s_mem_sum",  # Amount of main memory in Kubernetes
                        "k8s_pod_count",  # Number of Kubernetes pods
                        "k8s_volume_count",  # Number of Kubernetes volumes
                        "k8s_apiserver_url",  # URL of the API server
                        "k8s_cluster_name"  # Human-readable name of the cluster
                    ]
                }
            }],
            "responses": {
                "200": {
                    "description": "Returns a single information value as JSON dictionary with one entry. The key is the slug name."
                },
                "404": {
                    "description": "The information slug name is invalid."
                },
                "401": {
                    "description": "The JWT authentication information is missing."
                }
            }
        }
    )
    def get(self, request, version, info_slug):
        if info_slug in self.stats.keys():
            return Response({info_slug: self.stats[info_slug]()})
        else:
            raise NotFound


class InfoView(GenericAPIView):
    def get(self, request, version):
        result = {}
        for info_slug in InfoDetailView.stats.keys():
            result[info_slug] = reverse(viewname='info_detail', kwargs={'info_slug': info_slug}, request=request)
        return Response({'links': result})



