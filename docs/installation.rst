.. installation:

Installation
############

The latest official release of KubePortal is always available as `Docker image <https://hub.docker.com/r/troeger/kubeportal/>`__. The software is configured through environment variables (see :ref:`Configuration options`). 

It is *mandatory* to configure the public URLs used by the installation ``KUBEPORTAL_ALLOWED_URLS``.

It is *highly recommended* to configure at least one authentication method (``KUBEPORTAL_AUTH_...``) and the database storage.

KubePortal is expected to run inside the Kubernetes cluster it acts as frontend for. The API server is auto-detected from the pod running the software. Permissions must be given to the KubePortal namespace for allowing it to create new namespaces.

Installation with Kustomize
---------------------------

The `source code repository <https://github.com/troeger/kubeportal/tree/master/deployment/k8s>`_ offers Kustomize templates for installation. They perform the following activities:

  * A namespace ``kubeportal`` is created.

  * The namespace is configured with the neccessary `RBAC permissions <https://github.com/troeger/kubeportal/blob/master/deployment/k8s/base/rbac.yml>`_.

  * A persistent volume claim is created. 

  * A deployment is created:

    * It mounts the persistent volume at ``/data``. This allows you to easily configure an SQLite database for storage (``KUBEPORTAL_DATABASE_URL=sqlite:////data/kubeportal.sqlite3``).

    * The environment variables are read from a config map named ``kubeportal``. You could create that, for example, from a ``.env`` file with ``kubectl -n kubeportal create configmap kubeportal --from-env-file=.env``.

  * A service is created, which makes kubeportal available on the service name ``kubeportal`` at port 8000.    


Based on these templates, you could now define your own specialization and apply it to your cluster. Check the Kustomize docs for details about `using remote bases <https://kubectl.docs.kubernetes.io/pages/app_customization/bases_and_variants.html>`_.

First backend access
--------------------

After installation, first check if your configured frontend authentication method works as expected. A new frontend user should see this welcome screen:

.. image:: static/front_landing_new.png

You should now use the superuser login (see :ref:`Superuser access`) to create an admin group (see :ref:`User groups`) and add this first user to it.

Configuration options
---------------------

===================================== ============================================================================
Environment variable                  Description
===================================== ============================================================================
KUBEPORTAL_AUTH_TWITTER_KEY           Client key for OAuth when offering frontend Twitter login.
KUBEPORTAL_AUTH_TWITTER_SECRET        Client secret for OAuth when offering frontend Twitter login.
KUBEPORTAL_AUTH_GOOGLE_KEY            Client key for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_GOOGLE_SECRET         Client secret for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_GOOGLE_KEY            Client key for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_GOOGLE_SECRET         Client secret for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_OIDC_KEY              Client key when offering generic OpenID Connect login.
KUBEPORTAL_AUTH_OIDC_SECRET           Client secret when offering generic OpenID Connect login.
KUBEPORTAL_AUTH_OIDC_ENDPOINT         Endpoint URL when offering generic OpenID Connect login.
KUBEPORTAL_AUTH_OIDC_TITLE            Button title when offering generic OpenID Connect login.
KUBEPORTAL_AUTH_AD_DOMAIN             Domain when offering frontend Active Directory login, e.g. ``example.com``.
KUBEPORTAL_AUTH_AD_SERVER             Active directory server when offering frontend Active Directory login, e.g. ``192.168.1.1``. Not needed when equal to the A record behind the value of ``KUBEPORTAL_AUTH_AD_DOMAIN``.
KUBEPORTAL_API_SERVER_EXTERNAL        URL of the Kubernetes API server that works outside of the cluster, for end users. Automatically set to the internal URL if not set. 
KUBEPORTAL_SESSION_COOKIE_DOMAIN      The domain used for the user session cookie, e.g. ``.example.com``.
KUBEPORTAL_NAMESPACE_CLUSTERROLES     Kubernetes cluster roles that should be bound to the *default* service account of newly created Kubernetes namespaces, e.g. ``minimal-api,standard-api``.
KUBEPORTAL_BRANDING                   The human-readable name of your cluster.
KUBEPORTAL_ALLOWED_URLS               The portal URLs used by clients, eg. ``https://portal.foo.com:8000,http://example.com``. This is crucial for browser security headers, such as CORS.
KUBEPORTAL_INGRESS_TLS_ISSUER         The certificate issuer used for Ingress definitions created through the API. 
KUBEPORTAL_LANGUAGE_CODE              The locale for the web site, e.g. ``en-us``.
KUBEPORTAL_TIME_ZONE                  The time zone for the web site, e.g. ``UTC``.
KUBEPORTAL_ADMIN_NAME                 The name of the superuser, used only for email sending.
KUBEPORTAL_ADMIN_EMAIL                The email address of the superuser.
KUBEPORTAL_EMAIL_HOST                 The SMTP server used by the web site for sending mails.
KUBEPORTAL_DATABASE_URL               The database to be used as URL (see `formatting examples <https://github.com/jacobian/dj-database-url>`), e.g. ``sqlite:////data/kubeportal.sqlite3``.
KUBEPORTAL_REDIRECT_HOSTS             Hosts that redirect to the KubePortal web page, typically to perform OAuth authenication. Example: ``grafana.example.com, registry.example.com``.
KUBEPORTAL_ROOT_PASSWORD              The password to be used in the development environment for the `root` user. 
KUBEPORTAL_LOG_LEVEL_PORTAL           Sets the verbosity of the logging for the admin panel. [DEBUG, INFO, WARNING, ERROR, CRITICAL]
KUBEPORTAL_LOG_LEVEL_SOCIAL           Sets the verbosity of the logging for django.social. [DEBUG, INFO, WARNING, ERROR, CRITICAL]
KUBEPORTAL_LOG_LEVEL_REQUEST          Sets the verbosity of the logging for requests. [DEBUG, INFO, WARNING, ERROR, CRITICAL]
KUBEPORTAL_LAST_LOGIN_MONTHS_AGO      Sets how many months ago users have logged in to be considered old in the admin clean up page. Defaults to 12.
KUBEPORTAL_USE_ELASTIC                Boolean value whether or not to use elastic to access logs
KUBEPORTAL_ELASTIC_URL                The host address and port of the elastic interface.
KUBEPORTAL_ELASTIC_USERNAME           Username to authenticate user in elastic.
KUBEPORTAL_ELASTIC_PASSWORD           Password to authenticate user in elastic.
KUBEPORTAL_ELASTIC_INDEX              The index in which elastic queries.
===================================== ============================================================================
