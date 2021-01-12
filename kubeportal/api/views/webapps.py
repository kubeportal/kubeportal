from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import serializers, viewsets, mixins

from kubeportal.models.webapplication import WebApplication


class WebAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ('link_name', 'link_url')


@extend_schema_view(
    retrieve=extend_schema(summary='Get details about a web application.',
                           parameters=[OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH), ]),
)
class WebAppViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = WebAppSerializer

    def get_queryset(self):
        # Users can only request details of their own web applications..
        return self.request.user.web_applications(include_invisible=False)
