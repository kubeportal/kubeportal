import time
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .token import FernetToken, InvalidToken

from kubeportal.models import ClusterApplication



class FernetTokenView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard_fernet.html"

    def post(self, request):
        context = self.get_context_data()
        token = self.request.POST.get('token')
        fernet = FernetToken()
        verify_msg = ''
        if token:
            context['token'] = token     # reinsert into form
            # handle form post for token verification
            try:
                username = fernet.token_to_username(token)
            except InvalidToken:
                verify_msg = 'This token is invalid'
            else:
                if username == self.request.user.username:
                    stamp = fernet.extract_timestamp(token)
                    stamp = time.ctime(stamp)
                    verify_msg = 'This is your token, issued ' + stamp
                else:
                    verify_msg = "This is the token of somebody else's token"
        context['verify_msg'] = verify_msg
        return self.render_to_response(context)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard_index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['clusterapps'] = ClusterApplication.objects.all()
        return context


class ConfigDownloadView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'config.txt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.user.username
        context['username'] = username
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Content-Disposition'] = 'attachment; filename=config;'
        return response

    def test_func(self):
        return self.request.user.service_account != None


class ConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "dashboard_config.html"

    def test_func(self):
        return self.request.user.service_account != None
