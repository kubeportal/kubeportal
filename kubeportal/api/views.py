from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ModelViewSet

from django.contrib.auth import get_user_model
from kubeportal.api.serializers import UserSerializer
from kubeportal.models import UserState


class UserView(ModelViewSet, ListModelMixin):
    '''
    API endpoint that allows for users to queried
    '''
    queryset = get_user_model().objects.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer
