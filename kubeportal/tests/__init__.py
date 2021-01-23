import logging

logging.getLogger('KubePortal').setLevel(logging.ERROR)
logging.getLogger('django.request').setLevel(logging.ERROR)
logging.getLogger('django').setLevel(logging.ERROR)
