from django.contrib.auth.models import User
from django.db import models


class ServiceAccount(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
