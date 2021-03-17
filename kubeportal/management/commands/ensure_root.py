from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.conf import settings
from kubeportal.models.portalgroup import PortalGroup

class Command(BaseCommand):
    '''
        Make sure that superuser exists.

        In development mode, the superuser password is a default
        one (see settings.py), or is set through the KUBEPORTAL_ROOT_PASSWORD
        environment variable.

        In production mode, the superuser password is changed on every start
        and printed in the log output.
    '''

    def handle(self, *args, **option):
        # create django user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='root', is_superuser=True, is_staff=True)

        if hasattr(settings, 'ROOT_PASSWORD'):
            pw = settings.ROOT_PASSWORD
        else:
            pw = User.objects.make_random_password()

        user.password = make_password(pw)
        user.save()

        print("Superuser password is '{0}'.".format(pw))

        admin_groups = PortalGroup.objects.filter(can_admin=True) # auto-created by migration
        for g in admin_groups:
            g.members.add(user)
            g.save()