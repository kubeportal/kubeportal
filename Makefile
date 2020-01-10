SHELL = /bin/bash
VERSION = 0.2.0

.PHONY: check-venv

venv/bin/activate: requirements.txt
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	touch venv/bin/activate

# Shortcut for preparation of VirtualEnv
venv: venv/bin/activate

check-venv:
ifndef VIRTUAL_ENV
	$(error Please create a VirtualEnv with 'make venv' and activate it)
endif

# Run all tests.
tests: check-venv
	python ./manage.py test

# Update version numbers, commit and tag
bumpversion:
	bumpversion --verbose patch

dev-ssl: check-venv
	python ./manage.py runserver_plus --cert-file /tmp/cert.crt

docker:
	docker build -t troeger/kubeportal:$(VERSION) .

docker-run:
	docker run -it -p 8000:8000 troeger/kubeportal:$(VERSION)

run: venv
	venv/bin/python3 manage.py runserver

api-user: venv
	venv/bin/python3 manage.py createsuperuser --username api


api-token: venv
	venv/bin/python3 manage.py drf_create_token api

docker-dev: venv
	docker build -t troeger/kubeportal:dev -f Dockerfile-Dev .

docker-dev-stop:
	minikube stop
	minikube delete

docker-dev-run:
	minikube start --disk-size '2000mb'
	kubectl create -f ./deployment/k8s/namespace.yml \
				   -f ./deployment/k8s/rbac.yml \
				   -f ./deployment/k8s/service.yml \
				   -f ./deployment/k8s/deployment-dev.yml
	kubectl create secret generic mk-client-crt --from-file=mk-client-crt=${HOME}/.minikube/client.crt
	kubectl create secret generic mk-ca-crt     --from-file=mk-ca-crt=${HOME}/.minikube/ca.crt
	kubectl create secret generic mk-ca-key     --from-file=mk-ca-key=${HOME}/.minikube/ca.key
	kubectl create secret generic mk-ca-pem     --from-file=mk-ca-pem=${HOME}/.minikube/ca.pem
	kubectl create secret generic kube-config   --from-file=kube-config=${HOME}/.kube/config

# Re-create docker images and upload into registry
docker-push: docker
	docker login --username=troeger
	docker push troeger/kubeportal:$(VERSION)

# Clean temporary files
clean:
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean

# Clean cached Docker data and state
clean-docker:
	docker container prune
	docker volume prune
	docker system prune

# Build the HTML documentation from the sources.
docs: check-venv
	pushd docs; make html; popd


