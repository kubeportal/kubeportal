import logging, sys
from os import environ

logger = logging.getLogger('KubePortal')

# set log level (default to maximum verbosity)
logger.setLevel(logging.INFO)
if environ.get('KUBEPORTAL_LOG_LEVEL'):
    log_level = int(environ['KUBEPORTAL_LOG_LEVEL'])
    if log_level == 0:
        logger.setLevel(logging.CRITICAL)
    elif log_level == 1:
        logger.setLevel(logging.WARNING)
    elif log_level == 2:
        pass
    else:
        print("Unknown log level '{}'".format(log_level))
        print("Please check your KUBEPORTAL_LOG_LEVEL environment variable.")

handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

default_app_config = 'kubeportal.apps.KubePortalConfig'
