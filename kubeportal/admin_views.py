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

def sync_view(request):
    kubernetes.sync(request)
    return redirect('admin:index')

class CleanupView(LoginRequiredMixin, TemplateView):
    template_name = "admin/backend_cleanup.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['site_header'] = settings.BRANDING + " (Admin Backend)"
        context['title'] = "Clean Up"

        User = get_user_model()

        visible_namespaces = KubernetesNamespace.objects.filter(visible=True)
        counted_service_accounts = visible_namespaces.annotate(Count('service_accounts'))
        context['namespaces_no_portal_users'] = [ns for ns in counted_service_accounts if ns.service_accounts__count == 0]

        context['namespaces_no_pods'] = []
        pod_list = kubernetes.get_pods()
        for ns in visible_namespaces:
            ns_has_pods = False
            for pod in pod_list:
                if pod.metadata.namespace == ns.name:
                    ns_has_pods = True
                    break
            if not ns_has_pods:
                context['namespaces_no_pods'].append(ns)

        context['months'] = 12
        x_months_ago = datetime.now() - timedelta(days=30 * context['months']) # 30 days (1 month times the amount of months we look behind)
        context['old_service_accounts'] = list(User.objects.filter(last_login__lte = x_months_ago))
        return context
