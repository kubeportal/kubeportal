SHELL=/bin/bash
VERSION=0.2.0
GOOGLE_KEY=891177537513-sd1toqcvp7vl7e2bakvols27n1gh6h6n.apps.googleusercontent.com
GOOGLE_SECRET=qwoYQ9ktOra9b_JMr2_E19cx

# Run a Django dev server locally, together with Minikube
# Configuration: Debug
dev-run: minikube-start venv .env
	./venv/bin/python ./manage.py ensure_root --configuration=Development
	set -o allexport; source .env; set +o allexport; \
	./venv/bin/python ./manage.py runserver_plus --configuration=Development

# Run a staging test server in Minikube, based on the production image
# Server: uwsgi in Docker
# Configuration: Production
#
# Note: Terminating the running Kubeportal Docker container with Ctrl+C may
#       leave it in a dangled state. Call "docker system prune"
#       in such cases before the next execution of this target.
staging-run: staging-build minikube-start .env
	docker run -it --detach \
		--env-file .env \
		--name kubeportal_staging \
		-e KUBEPORTAL_CLUSTER_API_SERVER=$(shell minikube ip) \
		-p 8000:8000 troeger/kubeportal:staging
	# Copy and tweak config files so that Kubeportal can talk to Minikube
	docker cp ${HOME}/.kube kubeportal_staging:/root/
	docker exec kubeportal_staging sed -i 's#${HOME}/.minikube/#/root/.kube/#g' /root/.kube/config 
	docker cp ${HOME}/.minikube/ca.crt kubeportal_staging:/root/.kube/
	docker cp ${HOME}/.minikube/client.crt kubeportal_staging:/root/.kube/
	docker cp ${HOME}/.minikube/client.key kubeportal_staging:/root/.kube/
	docker attach kubeportal_staging

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

# Clean temporary files
clean: minikube-stop
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean

# Build the HTML documentation from the sources.
docs: venv
	pushd docs; make html; popd




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
	[ ! -z $(minikube status | grep Running | head -n 1) ] || minikube start

# Prepare a staging test Docker image
staging-build: minikube-start
	docker build -t troeger/kubeportal:staging .

# Prepare .env File for staging tests
.env:
	@echo "KUBEPORTAL_AUTH_GOOGLE_KEY=\"$(GOOGLE_KEY)\"" >> .env
	@echo "KUBEPORTAL_AUTH_GOOGLE_SECRET=\"$(GOOGLE_SECRET)\"" >> .env
