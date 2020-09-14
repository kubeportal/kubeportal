from django.views.generic.base import TemplateView, View, RedirectView
from django.http.response import HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django import forms


from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

from kubeportal.models import WebApplication
from kubeportal import kubernetes

import logging

logger = logging.getLogger('KubePortal')


class GoogleApiLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'portal_stats.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        User = get_user_model()
        try:
            context['usercount'] = User.objects.count()
            context['version'] = settings.VERSION
            context['k8sversion'] = kubernetes.get_kubernetes_version()
            context['apiserver'] = kubernetes.get_apiserver()
            context['numberofnodes'] = kubernetes.get_number_of_nodes()
            context['cpusum'] = kubernetes.get_number_of_cpus()
            context['memsum'] = kubernetes.get_memory_sum()
            context['numberofpods'] = kubernetes.get_number_of_pods()
            context['numberofvolumes'] = kubernetes.get_number_of_volumes()
        except Exception as e:
            logger.exception("Failed to fetch Kubernetes stats: {}".format(e))
        return context


class WelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "portal_welcome.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        # I am too tired to do this in a single Django query
        allowed_apps = []
        for group in self.request.user.portal_groups.all():
            for app in group.can_web_applications.all():
                if app not in allowed_apps:
                    if app.link_show:
                        allowed_apps.append(app)
                    else:
                        logger.debug('Not showing link to app "{0}" in welcome view. Although user "{1}"" is in group "{2}", link_show is set to False.'.format(app, self.request.user, group))
        context['clusterapps'] = allowed_apps

        User = get_user_model()
        context['portal_administrators'] = list(User.objects.filter(is_staff=True))
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "portal_settings.html"

    def update_settings(request):
        if request.method == "POST":
            new_default_email = request.POST['default-email']
            user = request.user
            if new_default_email in user.alt_mails:
                if user.email not in user.alt_mails:
                    user.alt_mails.append(user.email)
                user.email = new_default_email
                user.save()
                logger.info("Changed default email of user \"{}\" to \"{}\""
                            .format(user.username, new_default_email))
        return redirect("settings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = [g for g in self.request.user.portal_groups.all()]
        return context

class AccessRequestView(LoginRequiredMixin, RedirectView):
    def post(self, request):
        # create a form instance and populate it with data from the request:
        if 'selected-administrator' in request.POST:
            admin_username = request.POST['selected-administrator']
            if admin_username == "default":
                messages.add_message(request, messages.ERROR,
                                     "Please select an administrator from the dropdown menu.")
                return redirect("config")
            # get administrator and don't break if admin username can't be found
            User = get_user_model()
            admin = None
            try:
                admin = User.objects.get(username=admin_username)
            except Exception:
                logger.warning("Access request to unknown administrator username ({admin_username}).")

            # if administrator exists and access request was successfull...
            if admin and request.user.send_access_request(request, administrator=admin):
                request.user.save()
                messages.add_message(request, messages.INFO,
                                     'Your request was sent.')
            else:
                messages.add_message(request, messages.ERROR,
                                     'Sorry, something went wrong. Your request could not be sent.')
        return redirect("config")


class SubAuthRequestView(View):
    http_method_names = ['get']

    def _dump_request_info(self, request):
        logger.debug("Request details:")
        logger.debug("  Cookies: " + str(request.COOKIES))
        logger.debug("  Meta: " + str(request.META))
        logger.debug("  GET parameters: " + str(request.GET))
        logger.debug("  POST parameters: " + str(request.POST))

    def get(self, request, *args, **kwargs):
        webapp = get_object_or_404(WebApplication, pk=kwargs['webapp_pk'])
        if (not request.user) or (not request.user.is_authenticated):
            logger.debug(
                "Rejecting authorization for {} through sub-request, user is anonymous / not authenticated.".format(webapp))
            self._dump_request_info(request)
            # 401 is the expected fail code in ingress-nginx
            return HttpResponse(status=401)
        elif not webapp.can_subauth:
            logger.debug(
                "Rejecting authorization for {0} through sub-request for user {1}, subauth is not enabled for this app.".format(webapp, request.user))
            self._dump_request_info(request)
            return HttpResponse(status=401)
        elif not request.user.service_account:
            logger.debug(
                "Rejecting authorization for {0} through sub-request, user {1} has no service account.".format(webapp, request.user))
            self._dump_request_info(request)
            return HttpResponse(status=401)
        elif not request.user.can_subauth(webapp):
            logger.debug(
                "Rejecting authorization for {0} through sub-request, forbidden for user {1} through group membership constellation.".format(webapp, request.user))
            self._dump_request_info(request)
            return HttpResponse(status=401)
        else:
            logger.debug("Allowing authorization for {0} through sub-request (user {1}, service account '{2}:{3}').".format(
                webapp,
                request.user,
                request.user.service_account.namespace.name,
                request.user.service_account.name))
            response = HttpResponse()
            token = request.user.token
            if token:
                response['Authorization'] = 'Bearer ' + token
                return response
            else:
                logger.error("Error while fetching Kubernetes secret bearer token for user {0}, must reject valid  authorization for {1} through subrequest.".format(request.user, webapp))
                return HttpResponse(status=401)


class ConfigDownloadView(LoginRequiredMixin, TemplateView):
    template_name = 'config.txt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.user.username
        context['username'] = username
        User = get_user_model()
        context['portal_administrators'] = list(User.objects.filter(is_superuser=True))
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Content-Disposition'] = 'attachment; filename=config;'
        return response



class ConfigView(LoginRequiredMixin, TemplateView):
    template_name = "portal_config.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.user.username
        context['username'] = username
        User = get_user_model()
        context['portal_administrators'] = list(User.objects.filter(is_staff=True))
        return context
