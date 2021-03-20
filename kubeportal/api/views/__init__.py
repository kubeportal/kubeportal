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
- For uncached Kubernetes resources, we do not use the native UIDs,
  but a self-created portal identifier ("puid"),
  which is a concatenation of namespace and
  resource name with an illegal character in K8S, but not in URL world.
  This allows us to fetch a single pod / deployment / ... in the most
  efficient manner, since field selectors for the K8S metadata UID are
  not supported in the K8S API.
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
