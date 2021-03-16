from drf_spectacular.utils import extend_schema, OpenApiExample, extend_schema_serializer
from rest_framework import serializers, generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from kubeportal.k8s import kubernetes_api as api

import logging
logger = logging.getLogger('KubePortal')


class AnnotationSerializer(serializers.Serializer):
    """
    The API serializer for a annotation definition.
    """
    key = serializers.CharField()
    value = serializers.CharField()


class IngressPathSerializer(serializers.Serializer):
    path = serializers.CharField()
    service_name = serializers.CharField()
    service_port = serializers.IntegerField()


class IngressRuleSerializer(serializers.Serializer):
    """
    The API serializer for a ingress rule definition.
    """
    host = serializers.CharField()
    paths = serializers.ListField(child=IngressPathSerializer())


class IngressSerializer(serializers.Serializer):
    """
    The API serializer for an ingress definition.
    """
    name = serializers.CharField()
    creation_timestamp = serializers.DateTimeField(read_only=True)
    tls = serializers.BooleanField()
    annotations = serializers.ListField(child=AnnotationSerializer())
    rules = serializers.ListField(child=IngressRuleSerializer())


class IngressListSerializer(serializers.Serializer):
    ingress_urls = serializers.ListField(child=serializers.URLField())

class IngressRetrievalView(generics.RetrieveAPIView):
    serializer_class = IngressSerializer

    @extend_schema(
        summary="Get ingress by its UID."
    )
    def get(self, request, version, uid):
        ingress = api.get_ingress(uid)

        if not request.user.has_namespace(ingress.metadata.namespace):
            logger.warning(f"User '{request.user}' has no access to the namespace '{ingress.metadata.namespace}' of ingress '{ingress.metadata.uid}'. Access denied.")
            raise NotFound

        result_rules = []
        for k8s_rule in ingress.spec.rules:
            result_rule = {'host': k8s_rule.host,
                           'paths': [{'path': path.path,
                                      'service_name': path.backend.service_name,
                                      'service_port': path.backend.service_port}
                                     for path in k8s_rule.http.paths]}
            result_rules.append(result_rule)

        instance = IngressSerializer({
            'name': ingress.metadata.name,
            'creation_timestamp': ingress.metadata.creation_timestamp,
            'tls': True if ingress.spec.tls else False,
            'annotations': [{'key': list(ingress.metadata.annotations.keys())[0], 'value': list(ingress.metadata.annotations.values())[0]}],
            'rules': result_rules
        })
        return Response(instance.data)


class IngressesView(generics.CreateAPIView, generics.RetrieveAPIView):
    def get_serializer_class(self):
        if self.request.method == "GET":
            return IngressListSerializer
        if self.request.method == "POST":
            return IngressSerializer

    @extend_schema(
        summary="Get the list of ingresses in a namespace.",
        request=None,
        responses=IngressListSerializer
    )
    def get(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            ingresses = api.get_namespaced_ingresses(namespace)
            uids = [item.metadata.uid for item in ingresses]
            instance = IngressListSerializer({
                'ingress_urls': [reverse(viewname='ingress_retrieval', kwargs={'uid': uid}, request=request) for uid in uids]
            })
            return Response(instance.data)
        else:
            raise NotFound

    @extend_schema(
        summary="Create an ingress in a namespace.",
        request = IngressSerializer,
        responses = None
    )
    def post(self, request, version, namespace):
        if request.user.has_namespace(namespace):
            api.create_k8s_ingress(namespace,
                                   request.data["name"],
                                   request.data["annotations"],
                                   request.data["tls"],
                                   request.data["rules"]
                                   )
            return Response(status=201)
        else:
            raise NotFound
