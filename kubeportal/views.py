from django.views.generic.base import TemplateView, View
from django.contrib.auth.decorators import login_required
from .token import FernetToken

class IndexView(TemplateView):

    template_name = "index.html"


# XXX parameters to be configured:
server_url = 'TBD'
clustername = 'TBD'

# Access is protected by login, per url configuration
class ConfigView(TemplateView):

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
