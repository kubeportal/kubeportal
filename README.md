[![codecov](https://codecov.io/gh/kubeportal/kubeportal/branch/master/graph/badge.svg?token=9JYI6Q59H6)](undefined)

# Kubeportal Backend

The official end user documenation is here: https://kubeportal.readthedocs.io/en/latest/

## Quick start for developers

- Clone the repository.
- Run `make web-run` to start a development server with the Kubeportal backend.
- Run `make dev-run` to start a development server with the Kubeportal backend + Minikube integration. The latter must be installed.
- The developer mode automatically has a superuser account with name "root" and the password "rootpw."
- You can create a `.env` file in the project root for configuration. Check the manual for details: https://kubeportal.readthedocs.io/en/latest/installation.html#configuration-options
- Run `make test` to execute the test suite.

