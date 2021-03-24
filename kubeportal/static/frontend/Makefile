SHELL=/bin/bash
VERSION=0.3.14

start:
	docker-compose build
	docker-compose up

stop:
	docker-compose down

update-api:
	git subtree pull --prefix kubeportal-dev-api https://github.com/kubeportal/kubeportal-api-dev.git master --squash
