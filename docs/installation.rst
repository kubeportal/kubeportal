.. installation:

Installation
############

The latest official release of KubePortal is available as `Docker image <https://hub.docker.com/r/troeger/kubeportal/>`__. 

KubePortal is expected to run inside the Kubernetes cluster it works as a frontend for. The service account and API server are auto-detected from the pod it is running in. 

Example YML files for a Kustomize-based deployment are available in the `source code repository <https://github.com/troeger/kubeportal/tree/master/deployment/k8s>`_. You most likely need to add in Ingress definition for external reachability.

The application can be configured through environment variables:

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
===================================== ============================================================================

It is recommended to configure at least the following settings in production:

  - One authentication method (``KUBEPORTAL_AUTH_...``)
  - A reasonable path for the SQLite database in ``KUBEPORTAL_DATABASE_URL``, so that your user database persists on a mounted Kubernetes volume.
  - The externally visible URL of your Kubernetes API server (``KUBEPORTAL_API_SERVER_EXTERNAL``)

The log output of the KubePortal pod shows you the generated password for the *root* account. This account **only** works for the backend login page, which is available at `<KubePortal URL>/admin/`.

