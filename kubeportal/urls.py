from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include

from kubeportal import views

urlpatterns = [
    path('', LoginView.as_view(template_name='index.html', redirect_authenticated_user=True), name="index"),
    path('dashboard', views.DashboardView.as_view(), name="dashboard"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('social/', include('social_django.urls')),
    path('admin/', admin.site.urls),
]
