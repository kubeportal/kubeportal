from allauth.account.adapter import DefaultAccountAdapter
import logging

logger = logging.getLogger('KubePortal')

class AccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        '''
        The login template stores all incoming GET parameters in hidden POST fields.
        We take them here and convert them back to GET parameters for the redirect.
        '''
        if 'next' in request.POST:
            url = request.POST['next'] + '?'
            for key, value in request.POST.items():
                if key not in ['next', 'login', 'password', 'csrfmiddlewaretoken']:
                    url += "{}={}&".format(key, value)
            logger.info("Redirecting to {} due to 'next' POST parameter.".format(url))
            return url
        else:
            logger.debug("No redirection info found.")
            return super().get_login_redirect_url(request)
