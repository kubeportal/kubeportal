from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .token import FernetToken


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"


# XXX parameters to be configured:
server_url = 'TBD'
clustername = 'TBD'


class ConfigView(LoginRequiredMixin, TemplateView):

    template_name = 'config.txt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.user.username
        context['username'] = username
        context['server_url'] = server_url
        context['clustername'] = clustername
        fernet = FernetToken()
        context['token'] = fernet.username_to_token(username)
        return context
