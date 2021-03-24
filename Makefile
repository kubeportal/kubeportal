SHELL=/bin/bash
VERSION=0.6.8

.PHONY: docs

# Run a Django dev server locally, together with Minikube
# Configuration: Debug
back-run: minikube-start django-run

# Run a Django dev server locally, leaving out the Minikube startup
# This allows you to work against another cluster.
# Configuration: Debug
django-run: venv
	./venv/bin/python ./manage.py migrate --configuration=Development
	./venv/bin/python ./manage.py ensure_root --configuration=Development
	set -o allexport; source .env; set +o allexport; \
	./venv/bin/python ./manage.py runserver --configuration=Development

front-run: npm
	cd kubeportal/static/frontend && npm run serve

# Clean temporary files
clean: 
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean
	rm -rf htmlcov
	rm .coverage

# Build the HTML documentation from the sources.
docs: venv
	./venv/bin/python manage.py spectacular --file ./kubeportal/static/docs/openapi.yaml --configuration=Development
	pushd docs; make html; popd

# Runs the test suite
# You can restrict the tests bing executed by specifying the file:
# make test case=kubeportal/tests/test_admin.py
test: venv minikube-start
	./venv/bin/pytest ${case}

no-minikube-test: venv
	./venv/bin/pytest ${case}

# Run all tests and obtain coverage information.
coverage: venv 
	./venv/bin/pytest --cov=kubeportal --cov-report=html 

# Update version numbers, commit and tag
release-bumpversion:
	./venv/bin/bumpversion --verbose patch

release: release-bumpversion
	# bumpversion creates a git tag, which triggers the
	# Docker image build and push on Github
	git push --follow-tags

### Support functions, typically not for direct usage

# Checks if a virtualenv exists, and creates it in case
venv:
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements-prod.txt
	venv/bin/pip install -r requirements-dev.txt

npm:
	cd kubeportal/static/frontend && npm install

# Stops a Minikube environment
minikube-stop: minikube-check
	minikube stop
	minikube delete

# Start a Minikube environment
minikube-start: minikube-check
	(minikube status | grep Running) || minikube start
	kubectl config use-context minikube

# Check if minikube is installed
minikube-check:
	@test -f /usr/local/bin/minikube \
	|| test -f /usr/bin/minikube \
	|| test -f /bin/minikube \
        || test -f /opt/homebrew/bin/minikube \
	|| (echo ERROR: Minikube installation is missing on your machine. && exit 1)

