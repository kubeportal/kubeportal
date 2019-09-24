Configuring portal links
########################

Portal links are shown to users that have cluster access:

.. figure:: static/kubeportal1.png
    :alt: KubePortal landing page for cluster users.

They are configurable in the admin backend in the section *Links*.

The target URL can use placeholders, so that customized URLs are possible:

  - *{{namespace}}*: Inserts the configured Kubernetes namespace name for the portal user in the URL.
  - *{{serviceaccount}}*: Inserts the configured Kubernetes service account for the portal user in the URL.

Example for `Kubernetes Dashboard <https://github.com/kubernetes/dashboard>`_:

``https://dashboard.example.com/#!/overview?namespace={{namespace}}``
