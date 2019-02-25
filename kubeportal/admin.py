from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.contrib.auth.admin import UserAdmin
from django.template.response import TemplateResponse
from .models import KubernetesServiceAccount, KubernetesNamespace, ClusterApplication, User

from kubeportal.kubernetes import sync


class CustomAdminSite(admin.AdminSite):
    site_header = settings.BRANDING

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync', self.sync_view, name='sync'), ]

    def sync_view(self, request):
        ns_logs, svca_logs = sync()
        base_context = self.each_context(request)
        add_context = {'ns_logs': ns_logs, 'svca_logs': svca_logs}
        context = {**base_context, **add_context}
        return TemplateResponse(request, "admin/sync.html", context)


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'namespace']

    def has_change_permission(self, request, obj=None):
        return False


class KubernetesNamespaceAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

 
class PortalUserAdmin(UserAdmin):
    readonly_fields = ['username','is_superuser']
    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'service_account')
    fieldsets = (
        (None, {
            'fields': ('username','first_name','last_name','service_account', 'is_staff', 'is_superuser'),
        }),
    )

    def has_add_permission(self, request, obj=None):
        return False


admin_site = CustomAdminSite()
admin_site.register(User, PortalUserAdmin)
admin_site.register(KubernetesServiceAccount, KubernetesServiceAccountAdmin)
admin_site.register(KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(ClusterApplication)
