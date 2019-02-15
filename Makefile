SHELL = /bin/bash
VERSION = 0.1.0

.PHONY: docs check-venv

default: runserver

venv/bin/activate: kubeportal/requirements.txt 
	test -d venv || python3 -m venv venv
	venv/bin/pip install -r requirements.txt
	touch venv/bin/activate

# Shortcut for preparation of VirtualEnv
venv: venv/bin/activate

check-venv:
ifndef VIRTUAL_ENV
	$(error Please create a VirtualEnv with 'make venv' and activate it)
endif

runserver: check-venv 
	python ./manage.py migrate
	python ./manage.py runserver

# Build the HTML documentation from the sources.
docs: check-venv
	pushd docs; make html; popd

# Run all tests.
tests: check-venv 
	python ./manage.py test

# Run docker container with current code for interactive smoke testing
# Mounts the sources in the Docker container - so, as long as Apache
# detects the source code change, you should be able to do live patching
docker-test: 
	docker-compose -f deployment/docker-compose-test.yml up

docker-test-front-shell:
	docker exec -it deployment_kubeportal_1 bash

# Update version numbers, commit and tag 
bumpversion:
	bumpversion --verbose patch

# Re-create docker images and upload into registry
docker-push: build
	docker login --username=troeger
	docker build -t troeger/kubeportal:$(VERSION) kubeportal
	docker push troeger/kubeportal:$(VERSION)

# Clean temporary files
clean:
	find . -name "*.bak" -delete
	find . -name "__pycache__" -delete

# Clean HTML version of the documentation
clean-docs:
	rm -rf docs/formats

# Clean cached Docker data and state
clean-docker:
	docker container prune
	docker volume prune
	docker system prune

