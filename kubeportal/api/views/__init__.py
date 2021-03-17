"""
The Kubeportal REST API.

General design principles:

- API calls always return a JSON object resp. dictionary.
  See https://softwareengineering.stackexchange.com/questions/286293/whats-the-best-way-to-return-an-array-as-a-response-in-a-restful-api
  This means especially that list-only results are still wrapped in a single
  key dictionary (e.g. "/infos/")
- Fields with URL values are named "*_url", since the OpenAPI
  Swagger doc generation cannot map serializer URLField's into
  proper example values. This gives the developer a hint about the
  data type.
- Data structures are always described as DRF serializers, even when
  they are not really used in their original sense. This again enables
  the correct work of drf-spectacular for the API doc generation.
"""

from .bootstrapinfo import *
from .info import *
from .deployments import *
from .users import *
from .groups import *
from .pods import *
from .ingresses import *
from .ingresshosts import *
from .services import *
from .webapps import *
from .login import *
from .news import *
from .namespaces import *
from .serviceaccounts import *
from .persistentvolumeclaims import *
