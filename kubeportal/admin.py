from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.admin import UserAdmin
from .models import KubernetesServiceAccount, KubernetesNamespace, ClusterApplication, User

from kubeportal.kubernetes import sync


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync', self.sync_view, name='sync'), ]

    def sync_view(self, request):
        sync(request)
        return redirect('admin:index')


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'namespace']

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync(request)


class KubernetesNamespaceAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync(request)


class PortalUserAdmin(UserAdmin):
    readonly_fields = ['username', 'is_superuser']
    list_display = ('username', 'first_name', 'last_name',
                    'is_staff', 'service_account')
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'service_account', 'is_staff', 'is_superuser'),
        }),
    )

    def has_add_permission(self, request, obj=None):
        return False


admin_site = CustomAdminSite()
admin_site.register(User, PortalUserAdmin)
admin_site.register(KubernetesServiceAccount, KubernetesServiceAccountAdmin)
admin_site.register(KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(ClusterApplication)
