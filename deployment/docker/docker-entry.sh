#!/bin/bash
set -e

/code/manage.py migrate --configuration=Production

/usr/local/bin/uwsgi --http-auto-chunked \
                     --http-keepalive \
                     --wsgi-file /code/kubeportal/wsgi.py \
                     --master \
                     --pythonpath /code \
                     --uid 1000 \
                     --gid 1000 \
                     --threads 4 \
                     --http 0.0.0.0:8000 \
                     --static-map /static=/code/static-collected
