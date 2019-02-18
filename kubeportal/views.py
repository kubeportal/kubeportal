from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class DashboardView(LoginRequiredMixin, TemplateView):

    template_name = "dashboard.html"
