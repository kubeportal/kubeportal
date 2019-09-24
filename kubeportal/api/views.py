from django.views.decorators.csrf import csrf_exempt

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
class UserView(ModelViewSet):
    queryset = User.objects.filter(state=UserState.ACCESS_APPROVED)
    serializer_class = UserSerializer

    @action(methods=['get'], detail=True)
    def get(self, request):
        user_list = []
        for user in self.queryset:
            user_list.append(user.username)
        return Response(json.dumps(user_list))
