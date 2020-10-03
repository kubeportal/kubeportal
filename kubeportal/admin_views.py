from django.views.generic.base import TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, HttpResponse
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Count
from kubeportal import kubernetes, models
from kubeportal.models import KubernetesNamespace, KubernetesServiceAccount
from datetime import datetime, timedelta
import logging

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

        context['namespaces_no_service_acc'] = get_namespaces_without_service_accounts()
        context['namespaces_no_pods'] = get_namespaces_without_pods()
        context['months'] = settings.LAST_LOGIN_MONTHS_AGO
        context['inactive_users'] = get_inactive_users()
        return context

def get_namespaces_without_service_accounts():
    '''
    returns a list of namespaces without a service account
    '''
    visible_namespaces = KubernetesNamespace.objects.filter(visible=True)
    counted_service_accounts = visible_namespaces.annotate(Count('service_accounts'))
    return [ns for ns in counted_service_accounts if ns.service_accounts__count == 0]

def get_namespaces_without_pods():
    '''
    returns a list of namespaces without pods
    '''
    visible_namespaces = KubernetesNamespace.objects.filter(visible=True)
    namespaces_without_pods = []
    pod_list = kubernetes.get_pods()
    for ns in visible_namespaces:
        ns_has_pods = False
        for pod in pod_list:
            if pod.metadata.namespace == ns.name:
                ns_has_pods = True
                break
        if not ns_has_pods:
            namespaces_without_pods.append(ns)
    return namespaces_without_pods


def get_inactive_users():
    '''
    returns a list of users that haven't logged in x months ago.
    '''
    x_months_ago = datetime.now() - timedelta(days=30 * settings.LAST_LOGIN_MONTHS_AGO) # 30 days (1 month times the amount of months we look behind)
    User = get_user_model()
    return list(User.objects.filter(last_login__lte = x_months_ago))


def Prune(request):
    if request.method == 'POST':
        # copy immutable form data to mutable dict
        form = request.POST

        if not form['prune']:
            messages.add_message(request, messages.ERROR, "No prune method passed.")
            logger.warn("No prune method passed.")
            return redirect('admin:cleanup')

        if form['prune'] == 'namespaces-no-service-acc' or form['prune'] == 'namespaces-no-pods':
            namespaces = form.getlist('namespaces')
            KubernetesNamespace.objects.filter(name__in=namespaces).delete()
            messages.add_message(request, messages.WARNING, f"Pruning list of namespaces: [{', '.join(namespaces)}]")
            logger.warn(f"Pruning list of namespaces: [{', '.join(namespaces)}]")
        elif form['prune'] == 'inactive-users':
            users = form.getlist("users")
            User = get_user_model()
            User.objects.filter(username__in=users).delete()
            messages.add_message(request, messages.WARNING, f"Pruning list of users: [{', '.join(users)}]")
            logger.warn(f"Pruning list of users: [{', '.join(users)}]")

        return redirect('admin:cleanup')
    else:
        HttpResponse(401)
