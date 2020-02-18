Development Environment
#######################

There are two ways to launch the KubePortal development environment. One is for
editing code, the other to perform a staging test with the production version.

The following software is needed on your computer:

- Python 3
- Minikube (+ dependencies, such as libvirt or kvm2)
- GNU Make

The development environment will require you to create a .env file containing
- at least - the following environment variables.

- KUBEPORTAL_DATABASE_URL (usually sqlite:////data/kubeportal.sqlite3)
- KUBEPORTAL_AUTH_GOOGLE_SECRET
- KUBEPORTAL_AUTH_GOOGLE_KEY

Information about the variables can be found `here <installation.html>`_.

Note: If you have set up a minikube instance before using virtualbox you might
want to either delete the old instance or set up a new, named instance using kvm.
Otherwise minikube will refuse to start up.

You can always clean your computer from the running Minikube containers and temporary files with:

.. code-block:: bash

    make clean

Developing code
===============

.. code-block:: bash

    make dev-run

This command starts a minikube instance and the Django development server so that you can access the portal page at http://127.0.0.1:8000. Please note that Minikube is automatically changing your `kubectl` configuration.

You may want to let your local KubePortal instance talk to an external cluster, f.e. to test functionalities against production data. This is trivially possible by activating a different kubectl configuration. Whatever `kubectl` is talking to, your KubePortal instance is doing the same. 

Staging test
============

.. code-block:: bash

    make staging-run

This command:

  - Starts a minikube instance
  - Builds the production Docker image of KubePortal
  - Deploys it to the Minikube instance
  - Runs a port forwarding so that you can access the page at http://127.0.0.1:8000
  - It will use the environment variables defined in the .env file.

Note: You can check your current container status / logs not only via kubectl, but also
via the kubernetes dashboard. Just run `minikube dashboard`.

Logging
=======

Developers are able to set different log levels for KubePortal. By default, it will log as verbose as possible. You change the verbosity using the `KUBEPORTAL_LOG_LEVEL_*` environment variables. Please check the `installation manual <installation.html>`_
