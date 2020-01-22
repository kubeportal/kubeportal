Development Environment
#######################

There are 2 ways to launch the KubePortal development environment. One is for
editing code, the other to perform a staging test with the production version
of Kubeportal.

The following software is needed on your computer to start:

- Python 3
- Minikube (+ dependencies, such as libvirt or kvm2)
- GNU Make

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

This command starts a minikube instance, creates a default .env configuration
file (if missing) and starts the Django development server so that you can access the portal page at http://127.0.0.1:8000.

Staging test
============

.. code-block:: bash

    make staging-run

This command:

  - Starts a minikube instance
  - Creates a default .env configuration file (if missing)
  - Builds the production Docker image of KubePortal
  - Deploys it to the Minikube instance
  - Runs a port forwarding so that you can access the page at http://127.0.0.1:8000

Note: You can check your current container status / logs not only via kubectl, but also
via the kubernetes dashboard. Just run `minikube dashboard`.

