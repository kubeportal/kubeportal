[![codecov](https://codecov.io/gh/kubeportal/kubeportal/branch/master/graph/badge.svg?token=9JYI6Q59H6)](https://codecov.io/gh/kubeportal/kubeportal)

# Kubeportal

The official end user documenation is here: https://kubeportal.readthedocs.io/en/latest/

## Quick start for developers

The project consists of two pieces:

- The Vue.js frontend web application, which lives as Git subtree at `kubeportal/static/frontend`.
- The Django backend application, which provides the API and the admin pages.
  It also serves an older version of the frontend at `/classic`.

To start your work on the developer machine:

- Install Python, NPM and Minikube on your computer.
- Clone the repository.
- **Run `make front-run` to start an NPM development server for the Vue.js frontend project.**  
- **Run `make back-run` in another shell to start a Django development server for the backend project.**
- Go to the login page at `http://localhost:8000`.
- The developer mode automatically has a superuser account with name "root" and the password "rootpw."
- You may create a `.env` file in the project root for configuring the backend application. 
  This includes a change of the Kubernetes API server or the Active Directory login.
  Check the manual for details: https://kubeportal.readthedocs.io/en/latest/installation.html#configuration-options

## Update frontend sources

`git subtree pull --prefix kubeportal/static/frontend git@github.com:kubeportal/kubeportal-frontend.git master --squash`

## Running tests

Run `make test` to execute the test suite for the backend code. You can add the relative path of a specific test file, f.e. `make test case=kubeportal/tests/test_api.py`. 

The test suite assumes an existing Minikube installation on the machine, which is used for trying out the cluster interaction.

## Creating a release

Run `make release`:

- A new version number is generated and tagged.
- The sources are pushed to Github.
- Github CI/CD creates a new Docker image and pushes it to Docker Hub.

## Details about frontend <-> backend integration

The idea for integrating the Django and the Vue.js project was taken from here:

https://github.com/EugeneDae/django-vue-cli-webpack-demo

For the developer machine, it works like this:

- The Django dev server (*localhost:8000*) and the NPM dev server (*localhost:8086*) run in two terminals.
- The NPM dev server uses webpack in the background to compile Vue code into JS assets on the fly. The assets are served from main memory by the NPM server.
- A modified `kubeportal/static/frontend/vue.config.js` makes sure that Webpack generates a file `kubeportal/templates/vue-generated.html` on disk, based on a modified `kubeportal/static/frontend/public/index.html`. It contains all relevant JS `<script>` tags that point to the NPM dev server.
- The generated file is extended by `kubeportal/templates/vue-index.html`, which serves as the single page providing the Vue application. 
- The Django URL routing in `kubeportal/urls.py` ensures that all Vue-related URLs end up in a rendering of `kubeportal/templates/vue-index.html`. This is realized by a simple catch-all phrase, after all Django-implemented views are considered.
- The browser now loads all JS-sources from the NPM dev server, but the HTML page itself always from the Django dev server. This solves CORS problems (because the host origin remains the same) and makes a separate APP_BASE_URL configuration useless for the JS sources. The frontend does not need to mess around with environment variables. Hooray.

For production Docker images, it works like this:

- The Docker image build calls `npm run build`, which puts its output into `kubeportal/static/frontend_dist`. 
  It also includes the generation of  `kubeportal/templates/vue-generated.html`, as described above.
- In the next step, everything is moved into `kubeportal/static/frontend` and the original JS sources + node modules
  crap are removed from the Docker image.
- The normal Django `manage.py collectstatic` now prepares the static files folder for the web server, 
  which includes the compiled Vue.js sources.
- The tailored `vue.config.js` ensures that all generated assets have the correct base path inside the `static` folder being set.



