from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from os import environ


class Command(BaseCommand):
    ''' Make sure that superuser exists. '''

    def handle(self, *args, **option):
        # create django user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='root', is_superuser=True, is_staff=True)

        '''
        hard code password when running in development mode
        use random password as default in case something goes wrong
        if no root password is set as an environment variable, use 'rootpw'
        '''
        pw = None
        if environ['DJANGO_CONFIGURATION'] == 'Development':
            if environ.get('KUBEPORTAL_ROOT_PASSWORD'):
                pw = environ['KUBEPORTAL_ROOT_PASSWORD']
            else:
                pw = "rootpw"
        else:
            pw = User.objects.make_random_password()

        user.password = make_password(pw)
        user.save()

        if created:
            print("Superuser created, password is '{0}'.".format(pw))
        else:
            print("Superuser exists, password is '{0}'.".format(pw))
