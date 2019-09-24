from django.conf import settings
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
import oidc_provider
import logging
from . import models
from kubeportal.kubernetes import sync


logger = logging.getLogger('KubePortal')
User = get_user_model()


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING + " (Admin Backend)"

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync/', self.admin_view(self.sync_view), name='sync'), ]

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


def reject(modeladmin, request, queryset):
    for user in queryset:
        if user.reject(request):
            user.save()


reject.short_description = "Reject access request for selected users"


class PortalUserAdmin(UserAdmin):
    readonly_fields = ['username', 'is_superuser', 'state']
    list_display = ('username', 'first_name', 'last_name',
                    'is_staff', 'state', 'answered_by', 'service_account', 'approve_link')
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'is_staff')}),
        (None, {'fields': ('state', 'service_account', 'is_superuser')})
    )
    actions = [reject]

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

    def get_urls(self):
        urls = super().get_urls()
        # The admin_view() wrapper ensures access protection
        return [path('<uuid:approval_id>/approve/', self.admin_site.admin_view(self.approve_view), name='access_approve'),
                path('<uuid:approval_id>/reject/', self.admin_site.admin_view(self.reject_view), name='access_reject')] + urls

    def approve_view(self, request, approval_id):
        user = get_object_or_404(User, approval_id=approval_id)
        current_ns = user.service_account.namespace if user.service_account else None

        context = dict(
            self.admin_site.each_context(request),
            user=user,
            all_namespaces=models.KubernetesNamespace.objects.all(),
            current_ns=current_ns
        )
        if request.method == 'POST':
            if request.POST['choice'] == "approve_choose":
                new_ns = get_object_or_404(models.KubernetesNamespace, name=request.POST['approve_choose_name'])
                new_svc = get_object_or_404(models.KubernetesServiceAccount, namespace=new_ns, name="default")
                if user.approve(request, new_svc):
                    user.save()
            if request.POST['choice'] == "approve_create":
                new_ns = models.KubernetesNamespace(name=request.POST['approve_create_name'])
                new_ns.save()
                if sync(request):  # creates "default" service account automatically
                    new_svc = get_object_or_404(models.KubernetesServiceAccount, namespace=new_ns, name="default")
                    if user.approve(request, new_svc):
                        user.save()
                    else:
                        new_ns.delete()
            if request.POST['choice'] == "reject":
                if user.reject(request):
                    user.save()
            return redirect('admin:kubeportal_user_changelist')
        else:
            if user.has_access_approved or user.has_access_rejected:
                context['answered_decision'] = user.state
                context['answered_by'] = user.answered_by
            return TemplateResponse(request, "admin/approve.html", context)

    def reject_view(self, request, approval_id):
        user = User.objects.get(approval_id=approval_id)
        if user.reject(request):
            user.save()
        return redirect('admin:kubeportal_user_changelist')


admin_site = CustomAdminSite()
admin_site.register(models.User, PortalUserAdmin)
admin_site.register(models.KubernetesServiceAccount,
                    KubernetesServiceAccountAdmin)
admin_site.register(models.KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(models.Link)
admin_site.register(oidc_provider.models.Client)
admin_site.register(oidc_provider.models.UserConsent)
