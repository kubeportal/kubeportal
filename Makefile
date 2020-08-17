SHELL=/bin/bash
VERSION=0.3.14

start:
	docker-compose build
	docker-compose up

stop:
	docker-compose down

pull-frontend:
	git subtree pull --prefix kubeportal-frontend https://github.com/kubeportal/kubeportal-frontend.git master --squash

push-frontend:
	git subtree push --prefix kubeportal-frontend https://github.com/kubeportal/kubeportal-frontend.git master --squash

pull-api:
	git subtree pull --prefix kubeportal-api https://github.com/kubeportal/kubeportal.git fe-api --squash

push-api:
	git subtree push --prefix kubeportal-api https://github.com/kubeportal/kubeportal.git fe-api --squash

