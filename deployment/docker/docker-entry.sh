#!/bin/sh

/code/manage.py integrity_check --configuration=Production
/code/manage.py migrate --configuration=Production
/code/manage.py silk_clear_request_log --configuration=Production
/code/manage.py creatersakey --configuration=Production
/code/manage.py ensure_root --configuration=Production
/code/manage.py drf_create_token root --configuration=Production

/usr/local/bin/uwsgi --http-auto-chunked \
                     --http-keepalive \
                     --wsgi-file /code/kubeportal/wsgi.py \
                     --master \
                     --pythonpath /code \
                     --threads 4 \
                     --http 0.0.0.0:8000 \
                     --static-map /static=/code/static-collected
