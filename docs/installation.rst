.. installation:

Installation
############

The latest official release of KubePortal is available as `Docker image <https://hub.docker.com/r/troeger/kubeportal/>`__,
which can be deployed to your Kubernetes cluster in various ways.

Example YML files are available in the `source code repository <https://github.com/troeger/kubeportal/tree/master/deployment/k8s>`_.

The application can be configured through environment variables:

===================================== ============================================================================
Environment variable                  Description
===================================== ============================================================================
KUBEPORTAL_AUTH_TWITTER_KEY           Client key for OAuth when offering frontend Twitter login.
KUBEPORTAL_AUTH_TWITTER_SECRET        Client secret for OAuth when offering frontend Twitter login.
KUBEPORTAL_AUTH_GOOGLE_KEY            Client key for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_GOOGLE_SECRET         Client secret for OAuth when offering frontend Google login.
KUBEPORTAL_AUTH_AD_DOMAIN             Domain when offering frontend Active Directory login, e.g. ``example.com``.
KUBEPORTAL_AUTH_AD_SERVER             Active directory server when offering frontend Active Directory login, e.g. ``192.168.1.1``. Not needed when equal to the A record behind the value of ``KUBEPORTAL_AUTH_AD_DOMAIN``.
KUBEPORTAL_SESSION_COOKIE_DOMAIN      The domain used for the user session cookie, e.g. ``.example.com``.     
KUBEPORTAL_NAMESPACE_CLUSTERROLES     Kubernetes cluster roles that should be bound to the *default* service account of newly created Kubernetes namespaces, e.g. ``minimal-api,standard-api``.
KUBEPORTAL_BRANDING                   The human-readable name of your cluster.
KUBEPORTAL_CLUSTER_API_SERVER         The URL for your Kubernetes API server, e.g. ``https://k8smaster.example.com:6443``.
KUBEPORTAL_LANGUAGE_CODE              The locale for the web site, e.g. ``en-us``.
KUBEPORTAL_TIME_ZONE                  The time zone for the web site, e.g. ``UTC``.
KUBEPORTAL_ADMIN_NAME                 The name of the superuser, used only for email sending.
KUBEPORTAL_ADMIN_EMAIL                The email address of the superuser.
KUBEPORTAL_EMAIL_HOST                 The SMTP server used by the web site for sending mails.
KUBEPORTAL_DATABASE_URL               The database to be used as URL (see `formatting examples <https://github.com/jacobian/dj-database-url>`), e.g. ``sqlite:////data/kubeportal.sqlite3``. 
KUBEPORTAL_REDIRECT_HOSTS             Hosts that redirect to the KubePortal web page, typically to perform OAuth authenication. Example: ``grafana.example.com, registry.example.com``.
===================================== ============================================================================



It is recommended to configure at least the following settings:

  - One authentication method (``KUBEPORTAL_AUTH_...``)
  - A reasonable path for the SQLite database in ``KUBEPORTAL_DATABASE_URL``, so that your user database persists on a mounted Kubernetes volume.
  - ``KUBEPORTAL_CLUSTER_API_SERVER``, so that Kubeportal can talk to Kubernetes.

The `example YMLs <https://github.com/troeger/kubeportal/tree/master/deployment/k8s>`_ show how these variables can be set through a standard Kubernetes config map. Please note that we rely on
Kustomize for them.

After the first deployment, the log output of the KubePortal pod shows you the generated password for the *root* account once (!).
This account **only** works for the backend login page, which is available at `<KubePortal URL>/admin/`.

