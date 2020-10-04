from django.views.generic.base import TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, HttpResponse
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Count
from kubeportal import kubernetes, models
import logging

from kubeportal.models.kubernetesnamespace import KubernetesNamespace
from kubeportal.models import User

logger = logging.getLogger('KubePortal')


def sync_view(request):
    kubernetes.sync(request)
    return redirect('admin:index')


class CleanupView(LoginRequiredMixin, TemplateView):
    template_name = "admin/backend_cleanup.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['site_header'] = settings.BRANDING + " (Admin Backend)"
        context['title'] = "Clean Up"

        context['namespaces_no_service_acc'] = KubernetesNamespace.without_service_accounts()
        context['namespaces_no_pods'] = KubernetesNamespace.without_pods()
        context['months'] = settings.LAST_LOGIN_MONTHS_AGO
        context['inactive_users'] = User.inactive_users()
        return context


def prune(request):
    if request.method == 'POST':
        # copy immutable form data to mutable dict
        form = request.POST

        if not form['prune']:
            messages.add_message(request, messages.ERROR, "No prune method passed.")
            logger.warning("No prune method passed.")
            return redirect('admin:cleanup')

        if form['prune'] == 'namespaces-no-service-acc' or form['prune'] == 'namespaces-no-pods':
            namespaces = form.getlist('namespaces')
            KubernetesNamespace.objects.filter(name__in=namespaces).delete()
            messages.add_message(request, messages.WARNING, f"Pruning list of namespaces: [{', '.join(namespaces)}]")
            logger.warning(f"Pruning list of namespaces: [{', '.join(namespaces)}]")
        elif form['prune'] == 'inactive-users':
            users = form.getlist("users")
            User = get_user_model()
            User.objects.filter(username__in=users).delete()
            messages.add_message(request, messages.WARNING, f"Pruning list of users: [{', '.join(users)}]")
            logger.warning(f"Pruning list of users: [{', '.join(users)}]")

        return redirect('admin:cleanup')
    else:
        HttpResponse(401)
