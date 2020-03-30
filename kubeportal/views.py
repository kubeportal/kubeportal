from django.views.generic.base import TemplateView, View, RedirectView
from django.contrib.auth.views import LoginView
from django.http.response import HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import get_user_model

from kubeportal.models import WebApplication
from kubeportal import kubernetes

import logging

logger = logging.getLogger('KubePortal')


class IndexView(LoginView):
    template_name = 'index.html'
    redirect_authenticated_user = True

    def get_success_url_allowed_hosts(self):
        return settings.REDIRECT_HOSTS


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'portal_stats.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        User = get_user_model()
        context['usercount'] = User.objects.count()
        context['version'] = settings.VERSION
        try:
            context['stats'] = kubernetes.get_stats()
        except Exception:
            logger.exception("Failed to fetch Kubernetes stats")
            context['stats'] = None

        return context


class WelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "portal_welcome.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['clusterapps'] = WebApplication.objects.all()
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
        elif not request.user.can_subauth():
            logger.debug(
                "Rejecting authorization through subrequest, forbidden for user {0} through group membership.".format(request.user))
            self._dump_request_info(request)
            return HttpResponse(status=401)
        else:
            logger.debug("Allowing authorization through subrequest for user {0} with service account '{1}:{2}'.".format(
                request.user, request.user.service_account.namespace.name, request.user.service_account.name))
            response = HttpResponse()
            token = request.user.token
            if token:
                response['Authorization'] = 'Bearer ' + token
                return response
            else:
                logger.error("Error while fetching Kubernetes secret bearer token for user, must reject valid request.")
                return HttpResponse(status=401)



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
