import time
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from .token import FernetToken, InvalidToken


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard_index.html"

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

# XXX parameters to be configured:
server_url = 'TBD'
clustername = 'TBD'


class ConfigDownloadView(LoginRequiredMixin, TemplateView):
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

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Content-Disposition'] = 'attachment; filename=config;'
        return response


class ConfigView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard_config.html"

    def post(self, request):
        context = self.get_context_data()
        token = self.request.POST.get('token')
        fernet = FernetToken()
        verify_msg = ''
        if token:
            context['token'] = token       # reinsert into form
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
