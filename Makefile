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
	python manage.py runserver

api-user: venv
	python manage.py createsuperuser --username api

api-token: venv
	python manage.py drf_create_token api

# build local kubeportal docker image
docker-dev: venv
	rm -rf tmp && mkdir tmp
	cp ~/.minikube/{client.*,ca.*} ./tmp
	cp ~/.kube/config ./tmp
	docker build -t troeger/kubeportal:dev -f Dockerfile-Dev .
	rm -rf tmp

# launch a local docker instance of kubeportal for live code reload
docker-dev-run: venv
	[ ! -z $(minikube status | grep Running | head -n 1) ] || minikube start
	docker run -it \
		--env-file .env-dev \
		-e KUBEPORTAL_CLUSTER_API_SERVER=$(shell minikube ip) \
		-p 8000:8000 troeger/kubeportal:dev

# kill minikube instance
docker-dev-mk-stop:
	minikube stop
	minikube delete

# launch a minikube instance and deploy kubeportal on it
docker-dev-mk-run:
	minikube start --disk-size '8000mb'
	bash -c 'eval $$(minikube docker-env | sed '/^#/d') && docker build -t troeger/kubeportal:dev .'
	kubectl create -f ./deployment/k8s/namespace.yml \
				   -f ./deployment/k8s/rbac.yml \
				   -f ./deployment/k8s/service.yml \
				   -f ./deployment/k8s/deployment-dev.yml
	kubectl create secret generic mk-client-crt --from-file=${HOME}/.minikube/client.crt -n kubeportal
	kubectl create secret generic mk-ca-crt     --from-file=${HOME}/.minikube/ca.crt     -n kubeportal
	kubectl create secret generic mk-ca-key     --from-file=${HOME}/.minikube/ca.key     -n kubeportal
	kubectl create secret generic mk-ca-pem     --from-file=${HOME}/.minikube/ca.pem     -n kubeportal
	kubectl create secret generic kube-config   --from-file=${HOME}/.kube/config         -n kubeportal

# Re-create docker images and upload into registry
docker-push: docker
	docker login --username=troeger
	docker push troeger/kubeportal:$(VERSION)

# Clean temporary files
clean:
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete
	make -C docs clean
	rm -rf OME

# Clean cached Docker data and state
clean-docker:
	docker container prune
	docker volume prune
	docker system prune

# Build the HTML documentation from the sources.
docs: check-venv
	pushd docs; make html; popd


