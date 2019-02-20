from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Group
from .models import KubernetesServiceAccount, KubernetesNamespace, ClusterApplication


class RestrictedAdmin(admin.AdminSite):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin_site = RestrictedAdmin()
admin_site.site_header = settings.BRANDING + ' - Administration'
admin_site.register(User)
admin_site.register(Group)
admin_site.register(KubernetesServiceAccount)
admin_site.register(KubernetesNamespace)
admin_site.register(ClusterApplication)
