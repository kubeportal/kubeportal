import logging, sys

logger = logging.getLogger('KubePortal')

handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

default_app_config = 'kubeportal.apps.KubePortalConfig'
