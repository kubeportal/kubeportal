from django.contrib import admin
from django.conf import settings

admin_site = admin.AdminSite()
admin_site.site_header = settings.BRANDING + ' - Administration'
