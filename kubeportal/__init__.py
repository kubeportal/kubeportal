import logging, sys
from os import environ

def set_log_level(env_var_name, logger):
    '''
    Sets the log level based on environment variables for the given logger.
    '''
    # does the variable exist?
    if environ.get(env_var_name):
        log_level = int(environ[env_var_name])
        if log_level == 0:
            logger.setLevel(logging.CRITICAL)
        elif log_level == 1:
            logger.setLevel(logging.WARNING)
        elif log_level == 2:
            pass
        else:
            print("Unknown log level '{}'".format(log_level))
            print("Please check your '{}' environment variable.".format(env_var_name))
            
            handler = logging.StreamHandler(sys.stdout)
            logger.addHandler(handler)
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

set_log_level("KUBEPORTAL_LOG_LEVEL_REQUEST", logging.getLogger('django.request'))
set_log_level("KUBEPORTAL_LOG_LEVEL_PORTAL", logging.getLogger('KubePortal'))
set_log_level("KUBEPORTAL_LOG_LEVEL_SOCIAL", logging.getLogger('social'))


default_app_config = 'kubeportal.apps.KubePortalConfig'
