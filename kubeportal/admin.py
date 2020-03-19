from django.conf import settings
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.contrib.contenttypes.admin import GenericStackedInline
from oidc_provider.models import Client
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple
import logging
import uuid
from . import models
from kubeportal import kubernetes


logger = logging.getLogger('KubePortal')
User = get_user_model()


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING + " (Admin Backend)"

    def get_urls(self):
        urls = super().get_urls()
        return urls + [path('sync/', self.admin_view(self.sync_view), name='sync'), ]

    def sync_view(self, request):
        kubernetes.sync(request)
        return redirect('admin:index')


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'namespace']
    list_display_links = None

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        kubernetes.sync(request)

    def get_queryset(self, request):
        '''
        Show service accounts in namespaces being marked as non-visible
        only for superusers.
        '''
        qs = self.model.objects.get_queryset().order_by('namespace__name')
        if not request.user.is_superuser:
            qs = qs.filter(namespace__visible=True)
        return qs


def make_visible(modeladmin, request, queryset):
    queryset.update(visible=True)
make_visible.short_description = "Mark as visible"


def make_invisible(modeladmin, request, queryset):
    queryset.update(visible=False)
make_invisible.short_description = "Mark as non-visible"

class WebApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'link_show', 'client_id', 'client_secret']

    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Portal frontend', {
            'fields': ('link_show', 'link_name', 'link_url'),
        }),
        ('OpenID Connect', {
            'fields': ('oidc_client', ),
        }),
    )

    def client_id(self, instance):
        return instance.oidc_client.client_id if instance.oidc_client else ""
    client_id.short_description = "OIDC Client ID"

    def client_secret(self, instance):
        return instance.oidc_client.client_secret if instance.oidc_client else ""
    client_secret.short_description = "OIDC Client Secret"




class KubernetesNamespaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'visible', 'portal_users', 'created', 'number_of_pods']
    list_display_links = None
    list_filter = ['visible']
    ns_list = None
    pod_list = None
    actions = [make_visible, make_invisible]

    def portal_users(self, instance):
        return ','.join(User.objects.filter(service_account__namespace=instance).values_list('username', flat=True))

    def created(self, instance):
        if not self.ns_list:
            self.ns_list = kubernetes.get_namespaces()

        for ns in self.ns_list:
            if ns.metadata.name == instance.name:
                return ns.metadata.creation_timestamp
        return None
    created.short_description = "Created in Kubernetes"

    def number_of_pods(self, instance):
        if not self.pod_list:
            self.pod_list = kubernetes.get_pods()
        count = 0
        for pod in self.pod_list:
            if pod.metadata.namespace == instance.name:
                count += 1
        return count
    number_of_pods.short_description = "Number of pods"

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


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
        kubernetes.sync(request)

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


class PortalGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'members_list', 'app_list')

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ('members', 'web_applications'):
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def members_list(self, instance):
        return ', '.join(instance.members.values_list('username', flat=True))
    members_list.short_description = "Members"

    def app_list(self, instance):
        return ', '.join(instance.web_applications.all().values_list('name', flat=True))
    app_list.short_description = "Web applications"


class PortalUserAdmin(UserAdmin):
    readonly_fields = ['username', 'email', 'is_superuser']
    list_display = ('username', 'first_name', 'last_name',
                    'is_staff', 'state', 'answered_by', 'comments', 'email', 'approve_link')
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'comments', 'is_staff')}),
        (None, {'fields': ('state', 'answered_by', 'service_account', 'is_superuser')})
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
        '''
        This function handles new approval requests.
        It will use the user model's approve()/reject() functions to validate.
        After validation, the namespaces need to be created/deleted accordingly.
        '''
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
                if kubernetes.sync(request):  # creates "default" service account automatically
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

class OidcClientAdmin(admin.ModelAdmin):
    exclude = ('name', 'owner','client_type','response_types','jwt_alg', 'website_url', 'terms_url', 'contact_email', 'reuse_consent', 'require_consent', '_post_logout_redirect_uris', 'logo', '_scope')
    readonly_fields = ('client_secret',)

    def has_module_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if not obj.client_secret:
            obj.client_secret = uuid.uuid4()
        obj.name = obj.client_id
        obj._scope = "openid profile email"
        super().save_model(request, obj, form, change)

    class Meta:
        verbose_name = "OpenID Connect settings"


admin_site = CustomAdminSite()
admin_site.register(models.User, PortalUserAdmin)
admin_site.register(models.Group, PortalGroupAdmin)
admin_site.register(models.KubernetesServiceAccount,
                    KubernetesServiceAccountAdmin)
admin_site.register(models.KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(models.WebApplication, WebApplicationAdmin)
admin_site.register(Client, OidcClientAdmin)