Authentication provider for NGINX
#################################

Web applications offered through the `NGINX Ingress Controller <https://kubernetes.github.io/ingress-nginx/>`_ can be
protected with a KubePortal login. One use case for this is the `Kubernetes Dashboard <https://github.com/kubernetes/dashboard>`_.

The trick is to configure the Ingress controller to perform a 
`sub-auth request <https://kubernetes.github.io/ingress-nginx/examples/auth/oauth-external-auth/>`_ when the web
application is called. The link `<KubePortal URL>/subauthreq/` provides the neccessary
authentication check functionality. Please note that `KUBEPORTAL_SESSION_COOKIE_DOMAIN` must be set to a value
that matches both to your portal and application DNS name, e.g. `.example.com`, otherwise the login check will always fail.

Example:

.. code-block:: 

  apiVersion: extensions/v1beta1
  kind: Ingress
  metadata:
    name: kubernetes-dashboard
    namespace: kube-system
    annotations:
      kubernetes.io/ingress.class: nginx
      certmanager.k8s.io/cluster-issuer: letsencrypt
      nginx.ingress.kubernetes.io/auth-url: "https://portal.example.com/subauthreq"
      nginx.ingress.kubernetes.io/auth-signin: "https://portal.example.com"
      nginx.ingress.kubernetes.io/auth-response-headers: Authorization
  spec:
    tls:
    - secretName: "dashboard-tls"
      hosts:
      - "dashboard.example.com"
    rules:
    - host: "dashboard.example.com"
      http: 
        paths: 
        - path:
          backend:
            serviceName: kubernetes-dashboard
            servicePort: 80


If you are struggling with the authentication, don't forget to check the KubePortal log files for further information.
