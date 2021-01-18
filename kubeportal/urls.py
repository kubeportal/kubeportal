from django.conf.urls import include
from django.urls import path
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from oidc_provider.views import ProviderInfoView
from dj_rest_auth import views as dj_rest_views

from kubeportal import views
from kubeportal.api import views as api_views
from kubeportal.admin import admin_site

from rest_framework import permissions, routers

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path('subauthreq/<int:webapp_pk>/', cache_page(60 * 5)(views.SubAuthRequestView.as_view()), name='subauthreq'),
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('.well-known/openid-configuration', ProviderInfoView.as_view(), name='provider_info'),

    # frontend API views
    path('api/', api_views.BootstrapInfoView.as_view()),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('api/<str:version>/users/<int:user_id>/', api_views.UserView.as_view(), name='user'),
    path('api/<str:version>/groups/<int:group_id>/', api_views.GroupView.as_view(), name='group'),
    path('api/<str:version>/webapps/<int:webapp_id>/', api_views.WebAppView.as_view(), name='webapplication'),
    path('api/<str:version>/pods/<str:namespace>/', api_views.PodsView.as_view(), name='pods'),
    path('api/<str:version>/deployments/<str:namespace>/', api_views.DeploymentsView.as_view(), name='deployments'),
    path('api/<str:version>/services/<str:namespace>/', api_views.ServicesView.as_view(), name='services'),
    path('api/<str:version>/ingresses/<str:namespace>/', api_views.IngressesView.as_view(), name='ingresses'),
    path('api/<str:version>/login/', api_views.LoginView.as_view(), name='rest_login'),
    path('api/<str:version>/logout/', dj_rest_views.LogoutView.as_view(), name='rest_logout'),
    path('api/<str:version>/login_google/', views.GoogleApiLoginView.as_view(), name='api_google_login'),
    path('api/<str:version>/cluster/<str:info_slug>/', api_views.ClusterInfoView.as_view()),
    path('api/<str:version>/ingresshosts/', api_views.IngressHostsView.as_view()),

    # frontend web auth views
    path('accounts/', include('allauth.urls')),

    path('silk/', include('silk.urls', namespace='silk'))
]


