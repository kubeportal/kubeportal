from django.contrib import admin, messages
from django.conf import settings
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.admin import UserAdmin
import oidc_provider

from . import models
from kubeportal.kubernetes import sync


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING + " (Admin Backend)"

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync', self.sync_view, name='sync'), ]

    def sync_view(self, request):
        sync(request)
        return redirect('admin:index')


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'namespace']

    def has_change_permission(self, request, obj=None):
        '''
        The name and namespace of the service account can only be configured on
        creation, but is fixed after the first sync.
        '''
        if obj and obj.is_synced():
            return False
        else:
            return True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync(request)

    def has_delete_permission(self, request, obj=None):
        '''
        Disable deletion, even for superusers.
        '''
        return False

    def get_queryset(self, request):
        '''
        Show service accounts in namespaces being marked as non-visible
        only for superusers.
        '''
        qs = self.model.objects.get_queryset().order_by('namespace__name')
        if not request.user.is_superuser:
            qs = qs.filter(namespace__visible=True)
        return qs


class KubernetesNamespaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'visible']

    def has_change_permission(self, request, obj=None):
        '''
        When everything is read-only, the view is no longer a change view
        '''
        if obj and obj.is_synced() and not request.user.is_superuser:
            return False
        else:
            return True

    def get_readonly_fields(self, request, obj=None):
        '''
        The name of the namespace can only be configured on
        creation, but is fixed after the first sync.

        Only superusers can change the visibility flag, all the time.
        '''
        if obj:
            if request.user.is_superuser:
                return ['name', ]
            else:
                # Case as above in has_change_permission()
                return ['name', 'visible', ]
        else:
            if request.user.is_superuser:
                return []
            else:
                return ['visible', ]

    def has_delete_permission(self, request, obj=None):
        '''
        Disable deletion, even for superusers.
        '''
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync(request)

    def get_queryset(self, request):
        '''
        Show namespaces being marked as non-visible
        only for superusers.
        '''
        qs = self.model.objects.get_queryset().order_by('name')
        if not request.user.is_superuser:
            qs = qs.filter(visible=True)
        return qs


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

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        messages.warning(
            request, "KubePortal never deletes namespaces or service accounts in Kubernetes. You must do that manually.")

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        messages.warning(
            request, "KubePortal never deletes namespaces or service accounts in Kubernetes. You must do that manually.")

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['service_account'].queryset = models.KubernetesServiceAccount.objects.filter(
            namespace__visible=True)
        return super().render_change_form(request, context, *args, **kwargs)


admin_site = CustomAdminSite()
admin_site.register(models.User, PortalUserAdmin)
admin_site.register(models.KubernetesServiceAccount,
                    KubernetesServiceAccountAdmin)
admin_site.register(models.KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(models.Link)
admin_site.register(oidc_provider.models.Client)
admin_site.register(oidc_provider.models.UserConsent)
