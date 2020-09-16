from django.views.generic.base import TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import admin
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

        context['namespaces_no_portal_users'] = get_namespaces_without_service_accounts()
        context['namespaces_no_pods'] = get_namespaces_without_pods()
        context['months'] = settings.LAST_LOGIN_MONTHS_AGO
        context['inactive_service_accounts'] = get_inactive_service_accounts()
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


def get_inactive_service_accounts():
    '''
    returns a list of users that haven't logged in x months ago.
    '''
    x_months_ago = datetime.now() - timedelta(days=30 * settings.LAST_LOGIN_MONTHS_AGO) # 30 days (1 month times the amount of months we look behind)
    User = get_user_model()
    return list(User.objects.filter(last_login__lte = x_months_ago))


class PruneViews():
    def PruneNamespacesWithoutServiceAccounts(self):
        namespaces_without_service_accounts = get_namespaces_without_service_accounts()
        for ns in namespaces_without_service_accounts:
            logger.warn(f"Pruning {ns.name}!")
            ns.delete()
        return redirect("admin:cleanup")

    def PruneNamespacesWithoutPods(self):
        namespaces_without_pods = get_namespaces_without_pods()
        for ns in namespaces_without_pods:
            logger.warn(f"Pruning {ns.name}!")
            ns.delete()
        return redirect("admin:cleanup")

    def PruneInactiveServiceAccounts(self):
        inactive_service_accounts = get_inactive_service_accounts()
        for svc_acc in inactive_service_accounts:
            logger.warn(f"Pruning {svc_acc}!")
            svc_acc.delete()
        return redirect("admin:cleanup")
