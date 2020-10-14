from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from kubeportal import settings
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger('KubePortal')


class HideAdminForNonStaffMiddleware:
    '''
    When the user is not logged in, an attempt to access the admin interface
    is redirected to the frontend login page. This prevents Django from rendering its own backend
    login page.

    When the admin interface is accessed while the user is logged in, it is checked if the permissions
    are given, and a 404 is raised in case. Without that, non-staff users would end up in a redirect loop
    while trying to access the admin interface (illegally).
    '''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(reverse('admin:index')):
            if not request.user.is_authenticated:
                return redirect(reverse('account_login') + '?next=' + reverse('admin:index'))
            else:
                if not request.user.is_staff:
                    raise Http404()

        return self.get_response(request)


class CorsMiddleware:
    '''
    After spending endless hours fighting CORS with Kat-Hi,
    this is our final solution.
    We gave up on half-broken libraries for this issue.

    The list of valid origins is set with the KUBEPORTAL_ALLOWED_URLS
    environment variable.
    They need to match with the HTTP request header 'Origin' generated
    by the JavaScript API call.

    Please note that '*' is no longer an option for allowed origins:

    https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#Credentialed_requests_and_wildcards

    This middleware simply returns all needed headers with every response,
    so that we no longer need to understand the difference between preflight
    requests and the actual request.
    '''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not 'Origin' in request.headers:
            # This is not a CORS-related request.
            return response

        origin = request.headers['Origin']
        allowed_origins = settings.ALLOWED_URLS

        if len(allowed_origins) == 0:
            # Ok, the user forgot to configure KUBEPORTAL_ALLOWED_URLS.
            if settings.DEBUG == True: 
                # We call it the Kat-Hi mode. Just go on.
                logger.warning("KUBEPORTAL_ALLOWED_URLS is not set. Overriding CORS due to DEBUG mode.")
            else:
                # Whitelist is missing, so no CORS headers are added to the response.
                logger.error("KUBEPORTAL_ALLOWED_URLS is not set, so CORS origin check is not possible and the headers cannot be set. This will break JavaScript API calls.")
                return response
        else:
            # Nice, we have a whitelist for origins
            # We honor it, even in DEBUG mode, since the developer may try something here.
            if not origin in allowed_origins:
                # Given origin is not in the whitelist. This is an attack (0.00001%)
                # or a misconfiguration (99.99999% probability).
                #
                # God, I hate security.
                logger.error(f"Origin '{origin}' is not part of KUBEPORTAL_ALLOWED_URLS: {allowed_origins}. CORS headers cannot be set. This will break JavaScript API calls.")
                return response

        response["Access-Control-Allow-Origin"] = request.headers["Origin"]                    
        response["Vary"] = "Origin"  # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Origin
        response["Access-Control-Allow-Methods"] = "GET,HEAD,OPTIONS,POST,PUT,PATCH"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "Access-Control-Allow-Origin, Access-Control-Allow-Headers, " \
                                                   "Origin,Accept, X-Requested-With, Content-Type, " \
                                                   "Access-Control-Request-Method, Access-Control-Request-Headers," \
                                                   "Authorization, X-CSRFToken"
        return response


class AllowOptionsAuthentication(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return request.user and request.user.is_authenticated
