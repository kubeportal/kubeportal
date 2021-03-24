[![codecov](https://codecov.io/gh/kubeportal/kubeportal/branch/master/graph/badge.svg?token=9JYI6Q59H6)](https://codecov.io/gh/kubeportal/kubeportal)

# Kubeportal Backend

The official end user documenation is here: https://kubeportal.readthedocs.io/en/latest/

## Quick start for developers

The project consists of two pieces:

- The Vue.js frontend web application, which lives as Git subtree at `kubeportal/static/frontend`.
- The Django backend application, which provides the API and the admin pages.
  It also serves an older version of the frontend at `/classic`.

To start your work on the developer machine:

- Install Python, NPM and Minikube on your computer.
- Clone the repository.
- Run `make front-run` to start an NPM development server for the Vue.js frontend project.  
- Run `make back-run` in another shell to start a Django development server for the backend project.
- Go to the login page at `http://localhost:8000`.
- The developer mode automatically has a superuser account with name "root" and the password "rootpw."
- You may create a `.env` file in the project root for configuring the backend application. 
  Check the manual for details: https://kubeportal.readthedocs.io/en/latest/installation.html#configuration-options

## Running tests

Run `make test` to execute the test suite for the backend code. You can add the relative path of a specific test file, f.e. `make test case=kubeportal/tests/test_api.py`. 

The test suite assumes an existing Minikube installation on the machine, which is used for trying out the cluster interaction.

## Frontend <-> backend integration

The idea for integrating the Django and the Vue.js project was taken from here:

https://github.com/EugeneDae/django-vue-cli-webpack-demo

For the developer machine, it works like this:

- The Django dev server (*localhost:8000*) and the NPM dev server (*localhost:8086*) run in two terminals.
- The NPM dev server uses webpack in the background to compile Vue code into JS assets on the fly.
- A modified `kubeportal/static/frontend/vue.config.js` makes sure that Webpack generates a file `kubeportal/templates/vue-generated.html`, based on a modified `kubeportal/static/frontend/public/index.html`. It contains all relevant
  JS `<script>` tags that point to the NPM dev server.
- The generated file is extended by `kubeportal/templates/vue-index.html`, which serves as the single page providing the Vue application. 
- The Django URL routing in `kubeportal/urls.py` ensures that all Vue-related URLs end up in a rendering of `kubeportal/templates/vue-index.html`. This is realized by a simple catch-all phrase, after all Django-implemented views are considered.
- The browser now loads all JS-sources from the NPM dev server, but the HTML page itself always from the Django dev server. This solves CORS problems (because the host origin remains the same) and makes a separate APP_BASE_URL configuration useless for the JS sources. The frontend does not need to mess around with environment variables. Hooray.
