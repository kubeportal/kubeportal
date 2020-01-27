SHELL=/bin/bash
VERSION=0.2.0

# Run a Django dev server locally, together with Minikube
# Configuration: Debug
dev-run: minikube-start venv
	set -o allexport; source .env; set +o allexport; \
	KUBEPORTAL_CLUSTER_API_SERVER=$(shell minikube ip) \
	./venv/bin/python ./manage.py ensure_root --configuration=Development
	./venv/bin/python ./manage.py runserver_plus --configuration=Development

# Runs the production Docker image in Minikube
# Configuration: Production
staging-run: staging-build minikube-start
	kubectl apply -k ./deployment/k8s/staging/
	kubectl -n kubeportal delete configmap kubeportal --ignore-not-found=true
	kubectl -n kubeportal create configmap kubeportal --from-env-file=.env
	kubectl -n kubeportal logs deployment/kubeportal
	kubectl -n kubeportal port-forward svc/kubeportal 8000:8000

# Clean temporary files
clean: minikube-stop
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean

# Build the HTML documentation from the sources.
docs: venv
	pushd docs; make html; popd


### Functions for official releases


# Update version numbers, commit and tag
release-bumpversion:
	bumpversion --verbose patch

# Build the official Kuberportal docker image
release-build:
	docker build -t troeger/kubeportal:$(VERSION) .

# Upload the official Kuberportal image to Docker hub
release-push:
	docker login --username=troeger
	docker push troeger/kubeportal:$(VERSION)


### Support functions, typically not for direct usage


# Checks if a virtualenv exists, and creates it in case
venv:
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements.txt

# Stops a Minikube environment
minikube-stop:
	minikube stop
	minikube delete

# Start a Minikube environment
minikube-start:
	(minikube status | grep Running) || minikube start

# Prepare a staging test Docker image in the Minikube environment
# This works by utilizing the Docker environment inside Minikube
staging-build: minikube-start
	eval $$(minikube docker-env); docker build -t troeger/kubeportal:staging .
