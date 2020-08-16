from django.views.generic.base import RedirectView
from django.conf.urls import include
from django.urls import path
from oidc_provider.views import ProviderInfoView
from allauth.account import views as allauth_views
from allauth.socialaccount.providers.google import views as allauth_google_views
from dj_rest_auth import views as dj_rest_views

from kubeportal import views
from kubeportal.admin import admin_site
from kubeportal.views import GoogleApiLoginView

from kubeportal.api import views as api_views
from rest_framework import routers
router = routers.SimpleRouter()
router.register('users', api_views.UserView)

urlpatterns = [
    # frontend web views
    path('', RedirectView.as_view(url='/auth/login', permanent=False)),
    path('config/', views.ConfigView.as_view(), name='config'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('config/download/', views.ConfigDownloadView.as_view(content_type='text/plain'), name='config_download'),
    path('welcome/', views.WelcomeView.as_view(), name="welcome"),
    path('settings/', views.SettingsView.as_view(), name="settings"),
    path('settings/update', views.SettingsView.update_settings, name="update_settings"),
    path('access/request/', views.AccessRequestView.as_view(), name="access_request"),

    # backend web views
    path('admin/', admin_site.urls),

    # frontend auth provider views
    # Note: The OpenID Connect URL is /oidc/authorize
    path('subauthreq/<int:webapp_pk>/', views.SubAuthRequestView.as_view(), name='subauthreq'),
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('.well-known/openid-configuration', ProviderInfoView.as_view(), name='provider_info'),

    # frontend API views
    path('api/auth/login/', dj_rest_views.LoginView.as_view(), name='rest_login'),
    path('api/auth/logout/', dj_rest_views.LogoutView.as_view(), name='rest_logout'),

    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/google/login/', GoogleApiLoginView.as_view(), name='api_google_login'),
    path('api/', include(router.urls), name='api'),

    # frontend web auth views
    path("auth/login/", allauth_views.login, name="account_login"),
    path("auth/logout/", allauth_views.logout, name="account_logout"),
    path("auth/google/login/", allauth_google_views.oauth2_login, name="google_login"),
    path("auth/google/login/callback/", allauth_google_views.oauth2_callback, name="google_callback"),
    # needed by some reverse lookup in the allauth code
    path("auth/signup/", RedirectView.as_view(url='/signin/', permanent=False), name="account_signup"),
]
