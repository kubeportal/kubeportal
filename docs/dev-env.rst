Development Environment
#######################

If you plan on developing for KubePortal you will need a functioning
development environment. To create a homogenic development environment for
everyone, including a test cluster, we're using minikube to test the deployment
configuration.

There are 2 ways to launch the KubePortal development environment. One is for
editing code, the other to test deployment.

To launch a test instance we need to first set necessary build
environment variables. The build environment variables are specified seperately
in a `.env-dev` file which uses the same set of variables as `.env`.

Testing code with live reload
=============================

To test run your code, execute the following commands.

.. code-block:: bash

    cd /path/to/kubeportal
    make docker-dev
    make docker-dev-run

It will build and start up a docker container that will mount your current code
as a volume, which means it will automatically reload django whenever you make
a change to the source code.

Testing deployment
==================

The minikube cluster IP does not have to be set explicitly in `.env-dev` since
it will be set on the fly by the make instructions. The minimum set of
variables consists of:

- KUBEPORTAL_AUTH_AD_DOMAIN - Domain name of the active directory server

then we execute the following commands:

.. code-block:: bash

    cd /path/to/kubeportal
    make docker-dev-mk-run

It will prune minikube, rebuild it, then build the latest kubeportal:dev image
and lastly deploy the image on minikube.

Note: You can check your current container status not only via kubectl, but also
via the kubernetes dashboard. Just run `minikube dashboard`.

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
