from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from kubeportal.api.serializers import UserSerializer
from kubeportal.models import UserState
from django.contrib.auth import get_user_model

'''
API endpoint that allows for users to queried
'''
class UserView(ModelViewSet, ListModelMixin):
    queryset = get_user_model().objects.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer
