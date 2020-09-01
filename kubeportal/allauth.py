from allauth.account.adapter import DefaultAccountAdapter
import logging

logger = logging.getLogger('KubePortal')

class AccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        if 'next' in request.POST:
            url = request.POST['next']
            logger.info("Redirecting to {} due to 'next' POST parameter.".format(url))
            return url
        else:
            logger.debug("No redirection info found.")
            return super().get_login_redirect_url(request)
