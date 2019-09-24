from django.views.decorators.csrf import csrf_exempt

from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import View
import json

from rest_framework.response import Response

from kubeportal.api.serializers import UserSerializer
from kubeportal.models import User, UserState

'''
API endpoint that allows for users to queried
'''
class UserView(ModelViewSet, ListModelMixin):
    queryset = User.objects.all() #.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer
