import time
from django.views.generic.base import TemplateView, View, RedirectView
from django.contrib.auth.views import LoginView
from django.http.response import HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from django.http import JsonResponse
import json

from .token import FernetToken, InvalidToken

from kubeportal.models import Link, UserState, User

import logging
logger = logging.getLogger('KubePortal')


class FernetTokenView(LoginRequiredMixin, TemplateView):
    template_name = "portal_fernet.html"

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


class IndexView(LoginView):
    template_name = 'index.html'
    redirect_authenticated_user = True

    def get_success_url_allowed_hosts(self):
        return settings.REDIRECT_HOSTS


class WelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "portal_welcome.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['clusterapps'] = Link.objects.all()
        return context


class AccessRequestView(LoginRequiredMixin, RedirectView):
    pattern_name = 'welcome'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.send_access_request(self.request):
            self.request.user.save()
            messages.add_message(self.request, messages.INFO,
                                 'Your request was sent.')
        else:
            messages.add_message(self.request, messages.ERROR,
                                 'Sorry, something went wrong. Your request could not be sent.')
        return super().get_redirect_url(*args, **kwargs)


class SubAuthRequestView(View):
    http_method_names = ['get']

    def _dump_request_info(self, request):
        logger.debug("Request details:")
        logger.debug("  Cookies: " + str(request.COOKIES))
        logger.debug("  Meta: " + str(request.META))
        logger.debug("  GET parameters: " + str(request.GET))
        logger.debug("  POST parameters: " + str(request.POST))

    def get(self, request, *args, **kwargs):
        if (not request.user) or (not request.user.is_authenticated):
            logger.debug(
                "Rejecting authorization through subrequest, user is not authenticated.")
            self._dump_request_info(request)
            # 401 is the expected fail code in ingress-nginx
            return HttpResponse(status=401)
        elif not request.user.service_account:
            logger.debug(
                "Rejecting authorization through subrequest, user {0} has no service account.".format(request.user))
            self._dump_request_info(request)
            return HttpResponse(status=401)
        else:
            logger.debug("Allowing authorization through subrequest for user {0} with service account '{1}:{2}'.".format(
                request.user, request.user.service_account.namespace.name, request.user.service_account.name))
            response = HttpResponse()
            response['Authorization'] = 'Bearer ' + request.user.token
            return response

'''
Creates a list of approved users and responds with a JSON object containing them
'''
class UserExportView(View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        user_list = []
        for user in User.objects.filter(state=UserState.ACCESS_APPROVED):
            user_list.append(user.username)

        return JsonResponse(json.dumps(user_list), safe=False)

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
        '''
        Allow config download only if a K8S service account is set.
        Called by the UserPassesTestMixin.
        '''
        return self.request.user.service_account is not None


class ConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "portal_config.html"

    def test_func(self):
        '''
        Allow config view only if a K8S service account is set.
        '''
        return self.request.user.service_account is not None
