from allauth.account.adapter import DefaultAccountAdapter
import logging

logger = logging.getLogger('KubePortal')

class AccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        '''
        The login template stores all incoming GET parameters in hidden POST fields.

        A special case is "next", which is handled by Django (for redirection) before
        AllAuth can call our own handling here. Therefore, the login template stores
        the content of the "next"  GET parameter in the "rd" POST variable,
        to trigger this code in any case.

        The original GET parameters are attached to the redirection target.
        This should fix a couple of redirection problems with Kubeportal acting as
        OIDC provider.
        '''
        if 'rd' in request.POST:
            url = request.POST['rd']
            extra_params = {key: value for (key, value) in request.POST.items() if key not in ['rd', 'login', 'password', 'csrfmiddlewaretoken']}
            if len(extra_params) > 0:
                # Redirection target URL may already have encoded GET parameters, as with OAuth
                if '?' in url:
                    url += '&'
                else:
                    url += '?'
                for key, value in extra_params.items():
                    url += "{}={}&".format(key, value)
            logger.info("Redirecting to {} due to 'rd' POST parameter.".format(url))
            return url
        else:
            logger.debug("No redirection info found.")
            return super().get_login_redirect_url(request)
