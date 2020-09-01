from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse

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
