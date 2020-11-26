SHELL=/bin/bash
VERSION=0.5.4

.PHONY: docs

# Run a Django dev server locally, together with Minikube
# Configuration: Debug
dev-run: minikube-start web-run

# Run a Django dev server locally, leaving out the Minikube startup
# This allows you to work against another cluster.
# Configuration: Debug
web-run: venv
	./venv/bin/python ./manage.py migrate --configuration=Development
	./venv/bin/python ./manage.py ensure_root --configuration=Development
	set -o allexport; source .env; set +o allexport; \
	./venv/bin/python ./manage.py runserver --configuration=Development

# Clean temporary files
clean: 
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean
	rm -rf htmlcov
	rm .coverage

# Build the HTML documentation from the sources.
docs: venv
	pushd docs; make html; popd

# Runs the test suite
# You can restrict the tests bing executed by specifying the file:
# make test case=kubeportal/tests/test_admin.py
test: venv minikube-start
	./venv/bin/pytest ${case}

# Run all tests and obtain coverage information.
coverage: venv 
	./venv/bin/coverage run --omit 'venv/*' ./manage.py test --configuration=Development; ./venv/bin/coverage html; open htmlcov/index.html 

# Update version numbers, commit and tag
release-bumpversion:
	./venv/bin/bumpversion --verbose patch

release: release-build release-push

### Support functions, typically not for direct usage

# Build the official Kuberportal docker image
release-build:
	docker build -t troeger/kubeportal:$(VERSION) .

# Upload the official Kuberportal image to Docker hub
release-push:
	docker login --username=troeger
	docker push troeger/kubeportal:$(VERSION)

# Checks if a virtualenv exists, and creates it in case
venv:
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements-prod.txt
	venv/bin/pip install -r requirements-dev.txt

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
	|| (echo ERROR: Minikube installation is missing on your machine. && exit 1)

