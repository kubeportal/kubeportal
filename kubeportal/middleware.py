from social_django.middleware import SocialAuthExceptionMiddleware


class AuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    '''
    Custom version of the Social Auth exception middleware,
    so that Auth exceptions in DEBUG=True mode do not lead
    to a stack trace, but trigger the same behavior is an production.
    '''
    def raise_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is not None:
            return False
