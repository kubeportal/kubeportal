API
###

KubePortal provides an API for working with information stored in the portal database.
The interactive API documentation is available at `/api/docs`.

First call
----------
The initial call should be a `GET` call to the `/api/` endpoint of your installation.
It provides the CSRF token that is necessary for subsequent requests,
and the default API version currently supported by the installation:

.. code-block:: json

	{
	"csrf_token": "oZmEHPUxOn4VpP7hDpvJFx4Y1z8A7JY7ImNsve8r0f8TntUrw1PktuR4Xc1YQAgF",
	"portal_version": "v0.4.0",
	"default_api_version": "v1.4.0"
	}

The CRSF token must be sent in the  `X-CSRFToken` HTTP header of subsequent POST / PATCH / PUT requests.
It is not needed for GET requests:

.. code-block:: guess

	X-CSRFToken: oZmEHPUxOn4VpP7hDpvJFx4Y1z8A7JY7ImNsve8r0f8TntUrw1PktuR4Xc1YQAgF

Base URL for subsequent calls
------------------------------
The base URL for a given API version is `/api/<version>/`, so for the API version `v1.4.0`, the login method
is available at `/api/v1.4.0/login/`.


Security
--------
For most operations, authentication is needed. This is realized by providing credentials to the `login/` endpoint.
The response contains a JSON dictionary, which offers the authentication token under the `access_token` key.
Put the value into an authorization header field in subsequent request:

Response from `POST /api/<version>/login/` call with credentials:

.. code-block:: json

	{
	    "id": 1,
	    "firstname": "",
	    "access_token": "difhwoefhjwsefw"
	}

HTTP header in subsequent requests:

.. code-block:: guess

	Authorization: Bearer difhwoefhjwsefw

CORS headers are sent by this application, but the code behaves differently in debug mode and production mode.
In the latter case, it is mandatory to set the KUBEPORTAL_ALLOWED_URLS configuration option.
Check the server log output for details, in case of problems.

