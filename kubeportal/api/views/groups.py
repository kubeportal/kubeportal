from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from rest_framework import serializers, viewsets, mixins

from kubeportal.models.portalgroup import PortalGroup


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalGroup
        fields = ('name',)


@extend_schema_view(
    retrieve=extend_schema(summary='Get information about a user group in the portal.',
                           parameters=[OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH), ]),
)
class GroupViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = GroupSerializer

    def get_queryset(self):
        # Clients can only request details of the groups that they belong to.
        return self.request.user.portal_groups.all()
