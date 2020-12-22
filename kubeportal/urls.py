from django.conf.urls import include
from django.urls import path
from django.conf import settings
from django.views.generic.base import RedirectView
from oidc_provider.views import ProviderInfoView
from dj_rest_auth import views as dj_rest_views

from kubeportal import views
from kubeportal.api import views as api_views
from kubeportal.admin import admin_site

from rest_framework import permissions
from rest_framework_nested import routers

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


router = routers.SimpleRouter()
router.register('users', api_views.UserViewSet, basename='users')
router.register('cluster', api_views.ClusterViewSet, basename='cluster')
router.register('webapps', api_views.WebApplicationViewSet, basename='webapplications')
router.register('groups', api_views.GroupViewSet, basename='groups')

users_router = routers.NestedSimpleRouter(router, 'users', lookup='user')
users_router.register('webapps', api_views.WebApplicationViewSet, basename='user-webapplications')
users_router.register('groups', api_views.GroupViewSet, basename='user-groups')
users_router.register('pods'), api_views.PodViewSet, basename='user-pods')


schema_view = get_schema_view(
   openapi.Info(
      title="KubePortal API",
      default_version=settings.API_VERSION,
      contact=openapi.Contact(email="peter@troeger.eu"),
      license=openapi.License(name="GNU Affero General Public License v3.0"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

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
    path('api/<str:version>/login/', dj_rest_views.LoginView.as_view(), name='rest_login'),
    path('api/<str:version>/logout/', dj_rest_views.LogoutView.as_view(), name='rest_logout'),
    path('api/<str:version>/login_google/', views.GoogleApiLoginView.as_view(), name='api_google_login'),
    path('api/<str:version>/', include(router.urls)),
    path('api/<str:version>/', include(users_router.urls)),
    path('api/', api_views.BootstrapView.as_view()),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # frontend web auth views
    path('accounts/', include('allauth.urls')),

    path('silk/', include('silk.urls', namespace='silk'))
]


