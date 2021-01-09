from django.conf.urls import include
from django.urls import path
from django.conf import settings
from django.views.generic.base import RedirectView
from oidc_provider.views import ProviderInfoView
from dj_rest_auth import views as dj_rest_views

from kubeportal import views
from kubeportal.api import views as api_views
from kubeportal.admin import admin_site

from rest_framework import permissions, routers

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


viewsets = routers.SimpleRouter()
viewsets.register('users', api_views.UserViewSet, basename='users')
viewsets.register('groups', api_views.GroupViewSet, basename='groups')
viewsets.register('webapps', api_views.WebAppViewSet, basename='webapplications')
viewsets.register('pods', api_views.PodViewSet, basename='pods')
viewsets.register('deployments', api_views.DeploymentViewSet, basename='deployments')
viewsets.register('services', api_views.ServiceViewSet, basename='services')
viewsets.register('ingresses', api_views.IngressViewSet, basename='ingresses')

urlpatterns = [
    # frontend web views
    path('', RedirectView.as_view(query_string=True, url='/accounts/login/'), name='index'),
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
    path('api/', api_views.BootstrapInfoView.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/<str:version>/', include(viewsets.urls)),
    path('api/<str:version>/login/', dj_rest_views.LoginView.as_view(), name='rest_login'),
    path('api/<str:version>/logout/', dj_rest_views.LogoutView.as_view(), name='rest_logout'),
    path('api/<str:version>/login_google/', views.GoogleApiLoginView.as_view(), name='api_google_login'),
    path('api/<str:version>/cluster/<str:info_slug>/', api_views.ClusterInfoView.as_view()),

    # frontend web auth views
    path('accounts/', include('allauth.urls')),

    path('silk/', include('silk.urls', namespace='silk'))
]


