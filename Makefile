SHELL=/bin/bash
VERSION=0.3.14

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
	./venv/bin/python ./manage.py drf_create_token root --configuration=Development
	set -o allexport; source .env; set +o allexport; \
	./venv/bin/python ./manage.py runserver --configuration=Development

# Runs the production Docker image in Minikube
# Configuration: Production
staging-run: staging-build minikube-start
	kubectl apply -k ./deployment/k8s/staging/
	kubectl -n kubeportal delete configmap kubeportal --ignore-not-found=true
	kubectl -n kubeportal create configmap kubeportal --from-env-file=.env
	kubectl -n kubeportal logs deployment/kubeportal
	kubectl -n kubeportal port-forward svc/kubeportal 8000:8000

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
test: venv minikube-start
	./venv/bin/python ./manage.py test --configuration=Development

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

# Prepare a staging test Docker image in the Minikube environment
# This works by utilizing the Docker environment inside Minikube
staging-build: minikube-start
	eval $$(minikube docker-env); docker build -t troeger/kubeportal:staging .
