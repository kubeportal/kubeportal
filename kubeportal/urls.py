from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include

from kubeportal import views

urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('dashboard', views.DashboardView.as_view(), name="dashboard"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('social/', include('social_django.urls')),
    path('admin/', admin.site.urls),
]
