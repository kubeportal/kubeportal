Development Environment
#######################

If you plan on developing for KubePortal you will need a functioning
development environment. To create a homogenic development environment for
everyone, including a test cluster, we're using minikube. To launch a test
instance we need to first set necessary build environment variables. The build
environment variables are specified seperately in a `.env-dev` file which uses
the same set of variables as `.env`.

The minikube cluster IP does not have to be set explicitly in `.env.sh` since
it will be set on the fly by the make instructions. The minimum set of
variables consists of:

- KUBEPORTAL_AUTH_AD_DOMAIN - Domain name of the active directory server

then we execute the following commands:

.. code-block:: bash

    cd /path/to/kubeportal
    make docker-dev
    make docker-dev-run

Minikube will start if it is not already running and deploy the latest
kubeportal-dev image.

Build dependencies
==================

- docker
- docker-compose
- make
- python3-pip
- python3-virtualenv
- minikube
- kubernetes
- libvirt
- kvm2

Note: If you have set up a minikube instance before using virtualbox you might
want to either delete the old instance or set up a new, named instance using kvm.
Otherwise minikube will refuse to start up.
