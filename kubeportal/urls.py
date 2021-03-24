from django.conf.urls import include
from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from oidc_provider.views import ProviderInfoView
from dj_rest_auth import views as dj_rest_views
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.jwt_auth import get_refresh_view

from kubeportal import views
from kubeportal.api import views as api_views
from kubeportal.admin import admin_site

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [

    # classic frontend web views
    path('classic/', RedirectView.as_view(query_string=True, url='/classic/accounts/login/'), name='index'),
    path('classic/config/', views.ConfigView.as_view(), name='config'),
    path('classic/stats/', views.StatsView.as_view(), name='stats'),
    path('classic/config/download/', views.ConfigDownloadView.as_view(content_type='text/plain'), name='config_download'),
    path('classic/welcome/', views.WelcomeView.as_view(), name="welcome"),
    path('classic/settings/', views.SettingsView.as_view(), name="settings"),
    path('classic/settings/update', views.SettingsView.update_settings, name="update_settings"),
    path('classic/access/request/', views.AccessRequestView.as_view(), name="access_request"),
    path('classic/accounts/', include('allauth.urls')),

    # classic admin web views
    path('classic/silk/', include('silk.urls', namespace='silk')),
    path('classic/admin/', admin_site.urls),
    path('classic/tinymce/', include('tinymce.urls')),    

    # frontend auth provider views
    # Note: The OpenID Connect URL is /oidc/authorize
    path('subauthreq/<int:webapp_pk>/', cache_page(60 * 15)(views.SubAuthRequestView.as_view()), name='subauthreq'),
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('.well-known/openid-configuration', ProviderInfoView.as_view(), name='provider_info'),

    # API views
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/<str:version>/', api_views.BootstrapInfoView.as_view()),

    path('api/<str:version>/namespaces/<str:namespace>/', api_views.NamespaceView.as_view(), name='namespace'),
    path('api/<str:version>/namespaces/<str:namespace>/deployments/', api_views.DeploymentsView.as_view(), name='deployments'),
    path('api/<str:version>/namespaces/<str:namespace>/ingresses/', api_views.IngressesView.as_view(), name='ingresses'),
    path('api/<str:version>/namespaces/<str:namespace>/persistentvolumeclaims/', api_views.PersistentVolumeClaimsView.as_view(), name='pvcs'),
    path('api/<str:version>/namespaces/<str:namespace>/pods/', api_views.PodsView.as_view(), name='pods'),
    path('api/<str:version>/namespaces/<str:namespace>/services/', api_views.ServicesView.as_view(), name='services'),

    path('api/<str:version>/deployments/<str:puid>/', api_views.DeploymentRetrievalView.as_view(), name='deployment_retrieval'),
    path('api/<str:version>/ingresses/<str:puid>/', api_views.IngressRetrievalView.as_view(), name='ingress_retrieval'),
    path('api/<str:version>/persistentvolumeclaims/<str:puid>/', api_views.PersistentVolumeClaimRetrievalView.as_view(), name='pvc_retrieval'),
    path('api/<str:version>/pods/<str:puid>/', api_views.PodRetrievalView.as_view(), name='pod_retrieval'),
    path('api/<str:version>/services/<str:puid>/', api_views.ServiceRetrievalView.as_view(), name='service_retrieval'),
    path('api/<str:version>/serviceaccounts/<str:uid>/', api_views.ServiceAccountRetrievalView.as_view(), name='serviceaccount_retrieval'),

    path('api/<str:version>/users/<int:user_id>/', api_views.UserView.as_view(), name='user'),
    path('api/<str:version>/users/<int:user_id>/approval/', api_views.UserApprovalView.as_view(), name='user_approval'),
    path('api/<str:version>/groups/<int:group_id>/', api_views.GroupView.as_view(), name='group'),
    path('api/<str:version>/webapps/<int:webapp_id>/', api_views.WebAppView.as_view(), name='webapplication'),
    path('api/<str:version>/infos/', api_views.InfoView.as_view(), name='info_overview'),
    path('api/<str:version>/infos/<str:info_slug>/', api_views.InfoDetailView.as_view(), name='info_detail'),
    path('api/<str:version>/news/', api_views.NewsView.as_view(), name='news'),
    path('api/<str:version>/ingresshosts/', api_views.IngressHostsView.as_view()),

    path('api/<str:version>/login/', dj_rest_views.LoginView.as_view(), name='rest_login'),
    path('api/<str:version>/logout/', dj_rest_views.LogoutView.as_view(), name='rest_logout'),
    path('api/<str:version>/login_google/', views.GoogleApiLoginView.as_view(), name='api_google_login'),
    path('api/<str:version>/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/<str:version>/token/refresh/', get_refresh_view().as_view(), name='token_refresh'),

    # new frontend
    re_path(r'^.*$', views.VueView.as_view(), name='vue'),    
]


