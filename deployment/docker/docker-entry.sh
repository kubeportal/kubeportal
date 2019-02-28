#!/bin/bash
set -e

/code/manage.py migrate --configuration=Production

echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', 'myemail@example.com', 'admin')" | python /code/manage.py shell --configuration=Production

/usr/local/bin/uwsgi --http-auto-chunked \
                     --http-keepalive \
                     --wsgi-file /code/kubeportal/wsgi.py \
                     --master \
                     --pythonpath /code \
                     --threads 4 \
                     --http 0.0.0.0:8000 \
                     --static-map /static=/code/static-collected
