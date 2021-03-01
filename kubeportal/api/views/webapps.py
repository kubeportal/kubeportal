from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, extend_schema_serializer, \
    OpenApiExample
from rest_framework import serializers, generics

from kubeportal.models.webapplication import WebApplication


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            '',
            value={
                'link_name': 'Grafana',
                'link_url': 'https://monitoring.example.com',
                'category': 'MONITORING'
            },
            response_only=True
        ),
    ]
)
class WebAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApplication
        fields = ['link_name', 'link_url', 'category']

    def to_representation(self, data):
        data = super(WebAppSerializer, self).to_representation(data)
        link = data["link_url"]
        try:
            ns = self.context["request"].user.service_account.namespace.name
            svc = self.context["request"].user.service_account.name
        except:
            ns = ""
            svc = ""
        link = link.replace("{{{{namespace}}}}", ns).replace("{{{{serviceaccount}}}}", svc)
        data["link_url"] = link
        return data


@extend_schema_view(
    retrieve=extend_schema(summary='Get details about a web application.',
                           parameters=[OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH), ]),
)
class WebAppView(generics.RetrieveAPIView):
    serializer_class = WebAppSerializer
    lookup_url_kwarg = 'webapp_id'

    def get_queryset(self):
        # Users can only request details of their own web applications..
        webapps = self.request.user.web_applications(include_invisible=False)
        return webapps
