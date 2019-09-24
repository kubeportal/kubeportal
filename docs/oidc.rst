Authentication provider for OIDC
#################################

KubePortal operates as `OpenID Connect (OIDC) <https://openid.net/connect/>`_ provider, so web application such as `Grafana <https://grafana.com/>`_ can
use it for authentication.

The first step is to create a new OIDC client in the KubePortal backend. This generates a client ID
and client secret for your web application. Given these two, you can now configure your web application
for OIDC authentication:

  - The recommended authentication scopes are `openid`, `profile`, and `email`.
  - The link `<KubePortal URL>/oidc/authorize` provides the authorization page.
  - The link `<KubePortal URL>/oidc/token` provides the token information.
  - The link `<KubePortal URL>/oidc/userinfo` provides the OAuth API for fetching user information.

Example configuration for Grafana:

.. code-block:: 

	apiVersion: apps/v1beta2
	kind: Deployment
	metadata:
	  labels:
	    app: grafana
	  name: grafana
	  namespace: monitor
	spec:
	  replicas: 1
	  selector:
	    matchLabels:
	      app: grafana
	  template:
	    metadata:
	      labels:
	        app: grafana
	    spec:
	      containers:
	      - image: grafana/grafana:5.4.3
	        name: grafana
	        env:
	          - name: GF_AUTH_ANONYMOUS_ENABLED
	            value: "true"
	          - name: GF_AUTH_ANONYMOUS_ORG_NAME
	            value: "Internet"
	          - name: GF_AUTH_ANONYMOUS_ORG_ROLE
	            value: "Viewer"
	          - name: GF_AUTH_BASIC_ENABLED
	            value: "false"
	          - name: GF_SERVER_ROOT_URL
	            value: "https://monitoring.example.com"
	          - name: GF_AUTH_DISABLE_LOGIN_FORM
	            value: "true"
	          - name: GF_AUTH_GENERIC_OAUTH_ENABLED
	            value: "true"
	          - name: GF_AUTH_GENERIC_OAUTH_CLIENT_ID
	            value: "monitoring-service"  
	          - name: GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET
	            value: "c444e7641dc8cc5c638fhh83e6bc0f2288854cda355ed103b3e1118ea3cd3e5"
	          - name: GF_AUTH_GENERIC_OAUTH_ALLOW_SIGN_UP
	            value: "true"
	          - name: GF_AUTH_GENERIC_OAUTH_SCOPES
	            value: "openid profile email"
	          - name: GF_AUTH_GENERIC_OAUTH_AUTH_URL
	            value: "https://portal.example.com/oidc/authorize"
	          - name: GF_AUTH_GENERIC_OAUTH_TOKEN_URL
	            value: "https://portal.example.com/oidc/token"
	          - name: GF_AUTH_GENERIC_OAUTH_API_URL
	            value: "https://portal.example.com/oidc/userinfo"
	  ...

