from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import serializers, viewsets

from kubeportal.models.webapplication import WebApplication


class WebAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ('link_name', 'link_url')


@extend_schema_view(
    retrieve=extend_schema(summary='Get groups of this user.'),
    update=extend_schema(summary='Overwrite attributes of this user.'),
    partial_update=extend_schema(summary='Modify single attributes of this user.')
)
class WebAppViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WebAppSerializer

    def get_queryset(self):
        # Users can only request details of their own web applications..
        return self.request.user.web_applications(include_invisible=False)
