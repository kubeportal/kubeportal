from django.core.management.base import BaseCommand
from kubeportal.k8s import k8s_sync 

import logging

class Command(BaseCommand):
    def handle(self, *args, **option):
        k8s_sync.sync()

