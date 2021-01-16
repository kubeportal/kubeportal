from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_kubeportal_version():
    return 'v' + settings.VERSION


def get_user_count():
    return User.objects.count()


def get_cluster_name():
    return settings.BRANDING
