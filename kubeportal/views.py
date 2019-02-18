from django.views.generic.base import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(TemplateView):

    template_name = "index.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return super(IndexView, self).get(request)


class DashboardView(LoginRequiredMixin, TemplateView):

    template_name = "dashboard.html"
