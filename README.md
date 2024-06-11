This project is archived. For similar functionality, please check my new project at https://github.com/troeger/cloaksync.

# Kubeportal Backend

The official end user documenation is here: https://kubeportal.readthedocs.io/en/latest/

## Quick start for developers

- Clone the repository.
- Run `make web-run` to start a development server with the Kubeportal backend.
- Run `make dev-run` to start a development server with the Kubeportal backend + Minikube integration. The latter must be installed.
- The developer mode automatically has a superuser account with name "root" and the password "rootpw."
- You can create a `.env` file in the project root for configuration. Check the manual for details: https://kubeportal.readthedocs.io/en/latest/installation.html#configuration-options

## Running tests

Run `make test` to execute the test suite. You can add the relative path of a specific test file, f.e. `make test case=kubeportal/tests/test_api.py`. 

The test suite assumes an existing Minikube installation on the machine, which is used for trying out the cluster interaction.


