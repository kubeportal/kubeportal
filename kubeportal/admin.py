from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Group
from .models import Cluster

admin_site = admin.AdminSite()
admin_site.site_header = settings.BRANDING + ' - Administration'
admin_site.register(User)
admin_site.register(Group)
admin_site.register(Cluster)
