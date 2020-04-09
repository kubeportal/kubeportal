.. installation:

Installation
############

The latest official release of KubePortal is always available as `Docker image <https://hub.docker.com/r/troeger/kubeportal/>`__. 

Step 1: Define a configuration 
------------------------------

Create a configuration file, e.g. `.env`, which contains all relevant settings as environment variables. The options are:

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

Example for *.env* file:

.. code-block:: bash

  KUBEPORTAL_DATABASE_URL=sqlite:////data/kubeportal.sqlite3
  KUBEPORTAL_AUTH_AD_DOMAIN=example.com
  KUBEPORTAL_AUTH_AD_SERVER=1.2.3.4

Step 2: Create the config map
-----------------------------
KubePortal runs in the namespace `kubeportal`. This namespace must contain a config map with all your settings, which can be easily created from your `.env` file from the last step:

.. code-block:: bash

   kubectl create namespace kubeportal
   kubectl -n kubeportal create configmap kubeportal --from-env-file=.env

Step 3: Install in the cluster
------------------------------
KubePortal is expected to run inside a Kubernetes cluster. The service account and API server are auto-detected from the pod it is running in. Permissions for creating Kubernetes namespaces therefore must be given to its namespace. 

YML files for an according Kustomize-based deployment are available in the `source code repository <https://github.com/troeger/kubeportal/tree/master/deployment/k8s>`_. They also establish the neccessary RBAC settings for the application.

Please note that these Kustomize files already create a persistent volume claim to keep the database between restarts of the containers.

Step 4: Create an ingress
-------------------------
To make KubePortal reachable for your users, you must create a matching Ingress definition. The particular configuration depends on your environment.

Example:

.. code-block:: yml

   apiVersion: extensions/v1beta1
   kind: Ingress
   metadata:
     name: kubeportal
     namespace: kubeportal
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt
   spec:
     tls:
     - secretName: "cluster-subdomain-tls"
       hosts:
       - "cluster.example.com"
     rules:
     - host: "cluster.example.com"
       http: 
         paths: 
         - path: 
           backend:
             serviceName: kubeportal
             servicePort: 8000
