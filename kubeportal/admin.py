from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from .models import KubernetesServiceAccount, KubernetesNamespace, ClusterApplication


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync', self.sync_view, name='sync'), ]

    def sync_view(self, request):
        context = dict(self.each_context(request))
        return TemplateResponse(request, "admin/sync.html", context)


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class KubernetesNamespaceAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin_site = CustomAdminSite()
admin_site.register(User)
admin_site.register(KubernetesServiceAccount, KubernetesServiceAccountAdmin)
admin_site.register(KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(ClusterApplication)
