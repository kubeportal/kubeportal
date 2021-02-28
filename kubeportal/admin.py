from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
from django.http import HttpResponseServerError
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import redirect, get_object_or_404
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.utils.html import strip_tags
from django.forms import modelformset_factory, SelectMultiple, CheckboxSelectMultiple, modelform_factory
from oidc_provider.models import Client
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple
import logging
import uuid
from . import models, admin_views
from .k8s import k8s_sync, kubernetes_api as api
from .models.kubernetesnamespace import KubernetesNamespace
from .models.kubernetesserviceaccount import KubernetesServiceAccount
from .models.portalgroup import PortalGroup
from .models.webapplication import WebApplication
from .models.news import News

logger = logging.getLogger('KubePortal')
User = get_user_model()


class CustomAdminSite(admin.AdminSite):
    index_template = "admin/custom_index.html"
    site_header = settings.BRANDING + " (Admin Backend)"

    def get_urls(self):
        urls = super().get_urls()
        urls += [
                path('cleanup/', admin_views.CleanupView.as_view(), name='cleanup'),
                path('sync/', admin_views.sync_view, name='sync'),
                path('prune/', admin_views.prune, name='prune')
                ]
        return urls


class KubernetesServiceAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'namespace']
    list_display_links = None

    def has_delete_permission(self, request, obj=None):
        '''
        Disable deletion, even for superusers.
        '''
        return False

    def has_change_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

    def has_add_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        KubernetesServiceAccount.create_missing_in_cluster()

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


class WebApplicationAdminForm(forms.ModelForm):
    portal_groups = forms.ModelMultipleChoiceField(
        queryset=PortalGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=('Groups'),
            is_stacked=False
        )
    )

    class Meta:
        model = WebApplication
        fields = ('name', 'link_show', 'link_name',
                  'link_url', 'oidc_client', 'can_subauth')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['portal_groups'].initial = self.instance.portal_groups.all()

    def save(self, commit=True):
        webapp = super().save(commit=False)

        if commit:
            webapp.save()

        if webapp.pk:
            webapp.portal_groups.set(self.cleaned_data['portal_groups'])
            self.save_m2m()

        return webapp


class WebApplicationAdmin(admin.ModelAdmin):
    form = WebApplicationAdminForm

    list_display = ['name', 'portal_group_list', 'link_show', 'client_id',
                    'client_secret', 'client_redirect_uris',
                    'subauth_url', ]

    fieldsets = (
        (None, {
            'fields': ('name','category')
        }),
        ('Access allowed', {
            'fields': ('portal_groups',),
        }),
        ('Visibility', {
            'fields': ('link_show', 'link_name', 'link_url'),
        }),
        ('Integration', {
            'fields': ('oidc_client', 'can_subauth'),
        }),
    )

    def get_queryset(self, request):
        '''
        Helper implementation to have a request object somewhere else.
        '''
        qs = super().get_queryset(request)
        self.request = request
        return qs

    def subauth_url(self, instance):
        if instance.can_subauth:
            return self.request.build_absolute_uri(reverse('subauthreq', args=[instance.pk]))
        else:
            return ""

    def portal_group_list(self, instance):
        html_list = []
        for group in instance.portal_groups.all():
            group_url = reverse(
                'admin:kubeportal_portalgroup_change', args=[group.id, ])
            html_list.append(format_html(
                '<a href="{}">{}</a>', group_url, group.name))
        return format_html(', '.join(html_list))
    portal_group_list.short_description = "Allowed for"

    def client_id(self, instance):
        return instance.oidc_client.client_id if instance.oidc_client else ""
    client_id.short_description = "OIDC Client ID"

    def client_secret(self, instance):
        return instance.oidc_client.client_secret if instance.oidc_client else ""
    client_secret.short_description = "OIDC Client Secret"

    def client_redirect_uris(self, instance):
        return ', '.join(instance.oidc_client.redirect_uris) if instance.oidc_client else ""
    client_redirect_uris.short_description = "OIDC Redirect Targets"


class KubernetesNamespaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'visible',
                    'portal_users', 'created', 'number_of_pods']
    list_display_links = None
    list_filter = ['visible']
    ns_list = None
    pod_list = None
    actions = [make_visible, make_invisible]

    def portal_users(self, instance):
        return ','.join(User.objects.filter(service_account__namespace=instance).values_list('username', flat=True))

    def created(self, instance):
        if not self.ns_list:
            self.ns_list = api.get_namespaces()

        for ns in self.ns_list:
            if ns.metadata.name == instance.name:
                return ns.metadata.creation_timestamp
        return None
    created.short_description = "Created in Kubernetes"

    def number_of_pods(self, instance):
        if not self.pod_list:
            self.pod_list = api.get_pods()
        count = 0
        for pod in self.pod_list:
            if pod.metadata.namespace == instance.name:
                count += 1
        return count
    number_of_pods.short_description = "Number of pods"

    def has_change_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

    def has_add_permission(self, request, obj=None):
        if not request.user.is_superuser:
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
        KubernetesNamespace.create_missing_in_cluster()

    def get_queryset(self, request):
        '''
        Show namespaces being marked as non-visible
        only for superusers.
        '''
        qs = self.model.objects.get_queryset().order_by('name')
        if not request.user.is_superuser:
            qs = qs.filter(visible=True)
        return qs


class PortalGroupAdminForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=('Members'),
            is_stacked=False
        )
    )

    class Meta:
        model = PortalGroup
        fields = ('name', 'can_admin')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and 'members' in self.fields:
            self.fields['members'].initial = self.instance.members.all()

    def save(self, commit=True):
        group = super().save(commit=False)

        if commit:
            group.save()

        if group.pk:
            group.members.set(self.cleaned_data['members'])
            self.save_m2m()

        return group


class PortalGroupAdmin(admin.ModelAdmin):
    '''
    The group edit form disables name editing and membership management
    when a special group is shown. This is intended to prevent people
    from messing with group that have automated member management -
    users should only change the related mechanisms.

    In case something goes wrong, the superuser still has full edit rights.
    '''
    form = PortalGroupAdminForm     # implement reverse member management

    list_display = ('name', 'members_list', 'can_admin', 'app_list')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.is_special_group()  and not request.user.is_superuser:
                return ('name', 'members')
        return ()

    def get_fieldsets(self, request, obj=None):
        if obj:
            if obj.is_special_group() and not request.user.is_superuser:
                return (
                    (None, {'fields': ('name',)}),
                    ('Permissions', {'fields': ('can_admin', 'can_web_applications',)}),
                )
        return (
            (None, {'fields': ('name',)}),
            ('Members', {'fields': ('members',)}),
            ('Permissions', {'fields': ('can_admin', 'can_web_applications',)}),
        )


    def members_list(self, instance):
        from django.urls import reverse
        html_list = []
        for user in instance.members.all():
            user_url = reverse(
                'admin:kubeportal_user_change', args=[user.id, ])
            html_list.append(format_html(
                '<a href="{}">{}</a>', user_url, user.username))
        return format_html(', '.join(html_list))
    members_list.short_description = "Members"

    def app_list(self, instance):
        return ', '.join(instance.can_web_applications.all().values_list('name', flat=True))
    app_list.short_description = "Can use"


def make_assign_to_group_action(group):
    def assign_to_group(modeladmin, request, queryset):
        for user in queryset:
            user.portal_groups.add(group)
            messages.info(
                request, "User '{0}' is now member of '{1}'".format(user, group))

    assign_to_group.short_description = "Assign to group '{0}'".format(group)
    assign_to_group.__name__ = 'assign_to_group_{0}'.format(group.pk)

    return assign_to_group


def reject(modeladmin, request, queryset):
    for user in queryset:
        user.reject(request)
reject.short_description = "Reject access request for selected users"

def merge_users(modeladmin, request, queryset):
    if len(queryset) != 2:
        messages.warning(
            request, "Please choose exactly two users to merge.")
        return reverse('admin:index')
    primary, secondary = queryset.order_by('date_joined')

    # first check if any of the two accounts are rejected.
    # if any are, make sure to reject both as well.
    if primary.state == User.ACCESS_REJECTED or secondary.state == User.ACCESS_REJECTED:
        if primary.reject(request):
            primary.state = User.ACCESS_REJECTED
            messages.warning(
                request, F"Rejected cluster access for '{primary.username}'")

    # primary should be default. if secondary has more rights, then
    # secondary's values should be merged into primary.
    if primary.state != User.ACCESS_APPROVED and secondary.state == User.ACCESS_APPROVED:
        primary.state = User.ACCESS_APPROVED
        primary.approval_id = secondary.approval_id
        primary.answered_by = secondary.answered_by
    # iterate through the groups of secondary and add them to primary
    # if primary is not in group
    joined_groups = []
    for group in secondary.portal_groups.all():
        if group not in primary.portal_groups.all():
            primary.portal_groups.add(group)
            joined_groups.append(group)
    joined_groups = [str(g) for g in joined_groups]
    if joined_groups:
        messages.info(request, F"User '{primary.username}' joined the group(s) {joined_groups}")
    if primary.comments == "" or primary.comments is None:
        if  secondary.comments != "" and secondary.comments is not None:
            primary.comments = secondary.comments
    primary.save()
    secondary.delete()
    messages.info(request, F"The Users '{primary.username}' and '{secondary.username}' have been merged into '{primary.username}' and '{secondary.username}' has been deleted.")
merge_users.short_description = "Merge two users"


class PortalUserAdmin(UserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'comments',
                    'portal_group_list', 'state', 'answered_by', 'approve_link', 'alt_mails')
    fieldsets = (
        (None, {'fields': ('username', 'first_name',
                           'last_name', 'email', 'comments', 'alt_mails')}),
        (None, {'fields': ('state', 'answered_by', 'service_account')}),
        (None, {'fields': ('portal_groups',)})
    )
    actions = [reject, merge_users]
    list_filter = ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.service_account and obj.state == obj.ACCESS_APPROVED:
            # The admin manually changed the namespace of an approved user,
            # in order to "disable" the cluster access
            obj.state = obj.ACCESS_REJECTED
            obj.answered_by = request.user
            obj.save()
        if obj.service_account and not obj.state == obj.ACCESS_APPROVED:
            # The admin manually changed the namespace of an approved user,
            # in order to "enable" the cluster access without approval.
            obj.state = obj.ACCESS_APPROVED
            obj.answered_by = request.user
            obj.save()

    def portal_group_list(self, instance):
        from django.urls import reverse
        html_list = []
        for group in instance.portal_groups.filter(special_k8s_accounts=False, special_all_accounts=False):
            group_url = reverse(
                'admin:kubeportal_portalgroup_change', args=[group.id, ])
            html_list.append(format_html(
                '<a href="{}">{}</a>', group_url, group.name))
        return format_html(', '.join(html_list))
    portal_group_list.short_description = "Groups"

    def get_actions(self, request):
        actions = super(PortalUserAdmin, self).get_actions(request)

        for group in PortalGroup.objects.all():
            action = make_assign_to_group_action(group)
            actions[action.__name__] = (action,
                                        action.__name__,
                                        action.short_description)
        return actions

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        kwargs['widget'] = SortedFilteredSelectMultiple(
            attrs={'verbose_name': 'user groups'})
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return ['answered_by', 'state']
        else:
            return ['username', 'email', 'is_superuser', 'answered_by', 'state']

    def has_add_permission(self, request, obj=None):
        return request.user.is_superuser

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        messages.warning(
            request, "KubePortal never deletes namespaces or service accounts in Kubernetes. You must do that manually.")

    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        messages.warning(
            request, "KubePortal never deletes namespaces or service accounts in Kubernetes. You must do that manually.")

    def render_change_form(self, request, context, *args, **kwargs):
        if 'service_account' in context['adminform'].form.fields:
            context['adminform'].form.fields['service_account'].queryset = KubernetesServiceAccount.objects.filter(
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
        requesting_user = get_object_or_404(User, approval_id=approval_id)

        context = dict(
            self.admin_site.each_context(request),
            all_namespaces=KubernetesNamespace.objects.filter(visible=True),
            requesting_user=requesting_user
        )

        if request.method == 'POST':

            if request.POST['choice'] == "approve_choose":
                logger.info(f"Request for assigning '{requesting_user}' to existing namespace {request.POST['approve_choose_name']}")
                new_ns = get_object_or_404(
                    KubernetesNamespace, name=request.POST['approve_choose_name'])
                new_svc = get_object_or_404(
                    KubernetesServiceAccount, namespace=new_ns, name="default")
                requesting_user.approve(request, new_svc)

            if request.POST['choice'] == "approve_create":
                logger.info(f"Request for assigning user '{requesting_user}' to new namespace {request.POST['approve_create_name']}")
                ns = KubernetesNamespace.create_or_get(request.POST['approve_create_name'])
                if not ns:
                    return HttpResponseServerError()
                new_svc = get_object_or_404(KubernetesServiceAccount, namespace=ns, name="default")
                requesting_user.approve(request, new_svc)
            if request.POST['choice'] == "reject":
                logger.info(f"Request for rejecting approval request from {requesting_user}")
                requesting_user.reject(request)

            requesting_user.comments = request.POST['comments']

            requesting_user.portal_groups.clear()
            for group_id in request.POST.getlist('portal_groups'):
                group = get_object_or_404(PortalGroup, pk=int(group_id))
                logger.debug(f"Adding approved user {requesting_user} to group '{group}'")
                requesting_user.portal_groups.add(group)

            requesting_user.save()

            return redirect('admin:kubeportal_user_changelist')
        else:
            UserForm = modelform_factory(
                User, 
                fields= ('comments', 'portal_groups',), 
                widgets={'portal_groups': CheckboxSelectMultiple(attrs={'verbose_name': 'user groups'})}
            )
            user_form = UserForm(instance=requesting_user)
            context['user_form'] = user_form
            if requesting_user.has_access_approved or requesting_user.has_access_rejected:
                context['answered_by'] = requesting_user.answered_by
            return TemplateResponse(request, "admin/approve.html", context)

    def reject_view(self, request, approval_id):
        user = User.objects.get(approval_id=approval_id)
        user.reject(request)
        return redirect('admin:kubeportal_user_changelist')


class OidcClientAdmin(admin.ModelAdmin):
    exclude = ('name', 'owner', 'client_type', 'response_types', 'jwt_alg', 'website_url', 'terms_url',
               'contact_email', 'reuse_consent', 'require_consent', '_post_logout_redirect_uris', 'logo', '_scope')
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


class NewsAdmin(admin.ModelAdmin):
    exclude = ('author',)
    list_display = ('title', 'modified', 'priority','author')

    def save_model(self, request, obj, form, change):
        obj.author = request.user
        super().save_model(request, obj, form, change)



admin_site = CustomAdminSite()
admin_site.register(User, PortalUserAdmin)
admin_site.register(PortalGroup, PortalGroupAdmin)
admin_site.register(KubernetesServiceAccount,
                    KubernetesServiceAccountAdmin)
admin_site.register(KubernetesNamespace, KubernetesNamespaceAdmin)
admin_site.register(WebApplication, WebApplicationAdmin)
admin_site.register(Client, OidcClientAdmin)
admin_site.register(News, NewsAdmin)
