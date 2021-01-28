"""
The KubePortal test suite.

The test suite heavily relies on the concept of fixture in PyTest. They are included
from multiple sources:

- The built-in fixtures offered by PyTest itself.
- The fixtures from the pytest-django library, such as "admin_user".
- The fixtures from the pytest-mock library (mocker).
- The custom fixtures in this project, see confest.py.
"""

import logging

logging.getLogger('KubePortal').setLevel(logging.DEBUG)
logging.getLogger('django.request').setLevel(logging.ERROR)
logging.getLogger('django').setLevel(logging.INFO)
