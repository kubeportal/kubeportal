from django.views.generic.base import RedirectView
from django.conf.urls import include
from django.urls import path
from oidc_provider.views import ProviderInfoView

from kubeportal import views
from kubeportal.admin import admin_site

from kubeportal.api import views as api_views
from rest_framework import routers
router = routers.SimpleRouter()
router.register('users', api_views.UserView)

urlpatterns = [
    path('config/', views.ConfigView.as_view(), name='config'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('subauthreq/<int:webapp_pk>/', views.SubAuthRequestView.as_view(), name='subauthreq'),
    path('config/download/', views.ConfigDownloadView.as_view(content_type='text/plain'), name='config_download'),
    path('welcome/', views.WelcomeView.as_view(), name="welcome"),
    path('settings/', views.SettingsView.as_view(), name="settings"),
    path('settings/update', views.SettingsView.update_settings, name="update_settings"),
    path('access/request/', views.AccessRequestView.as_view(), name="access_request"),
    path('accounts/', include('allauth.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=True)),
    path('admin/login/', RedirectView.as_view(url='/accounts/login/?next=/admin/', permanent=True)),
    path('admin/', admin_site.urls),
    # Note: The OpenID Connect URL is /oidc/authorize
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('.well-known/openid-configuration', ProviderInfoView.as_view(), name='provider_info'),
    path('api/', include(router.urls), name='api'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls'))


]
